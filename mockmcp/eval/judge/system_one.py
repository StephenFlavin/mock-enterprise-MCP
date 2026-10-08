"""Decision-model judges over TypeSafe's System One API (`POST /v1/systemone`): Jev (TypeSafe direct, OpenRouter, LLM
Gateway) and Cygnet (local blockbrain shim). The model never sees the whole payload and never picks the outcome: the
payload is decomposed into small closed questions with focused states (decompose.py), answered here, and combined in code.

Stdlib HTTP only (urllib): the official SDK is pre-1.0 and may reject the dummy key a keyless local Cygnet needs."""
import hashlib
import json
import os
import random
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

from .base import Judge, register

CHARS_PER_TOKEN = 2.7    # JSON states, calibrated in this repo against real usage
SAFETY = 0.10            # budget = limit minus 10%
RETRYABLE = {408, 429, 529}

# context_tokens: total per request (all questions + state); pass_tokens: state + longest question (Cygnet: every question
# is a separate pass, so only this applies). state_tokens: per-question state budget after question text and margin.
# confidence: how the backend's own `confidence` is defined (Jev: top-prob / distance-aware; Cygnet: (K*p_max-1)/(K-1)).
# concurrency: requests in flight per process. thresholds: (reject_at_or_below, accept_at_or_above), until calibrated.
# benefit_of_doubt: families whose uncertain answers resolve in the model's favour when judging alone (still undecided,
# so a cascade escalates them).
PROFILES = {
    "jev": {"base_url": "https://api.typesafe.ai", "model": "jev-1.13.0", "key_env": "TYPESAFE_API_KEY",
            "context_tokens": 64000, "pass_tokens": 32000, "state_tokens": 28000, "per_pass": False, "confidence": "jev",
            "concurrency": 8, "precision": None, "usd_per_m_input": 0.042, "thresholds": {"default": [0.25, 0.75]}},
    "jev-openrouter": {"base_url": "https://openrouter.ai/api", "model": "typesafe/jev-1.13", "key_env": "OPENROUTER_API_KEY",
                       "context_tokens": 32000, "pass_tokens": 32000, "state_tokens": 28000, "per_pass": False,
                       "confidence": "jev", "concurrency": 8, "precision": None, "usd_per_m_input": None,
                       "thresholds": {"default": [0.25, 0.75]}},
    "jev-llmgateway": {"base_url": "https://api.llmgateway.io", "model": "jev-1.13.0", "key_env": "LLM_GATEWAY_API_KEY",
                       "context_tokens": 64000, "pass_tokens": 32000, "state_tokens": 28000, "per_pass": False,
                       "confidence": "jev", "concurrency": 8, "precision": None, "usd_per_m_input": None,
                       "thresholds": {"default": [0.25, 0.75]}},
    "cygnet": {"base_url": "http://127.0.0.1:8010", "model": "cygnet", "key_env": "CYGNET_API_KEY",
               "context_tokens": 16384, "pass_tokens": 16384, "state_tokens": 12000, "per_pass": True, "confidence": "cygnet",
               "concurrency": 2, "precision": "bf16", "usd_per_m_input": 0.0,
               # grounding: whether an unmatched figure is derived needs arithmetic the model is not asked to do; on 80 gold
               # labels its rejections were 10 of 13 wrong (code catches provable errors), so it never rejects there and an
               # uncertain answer is resolved in the model's favour alone but escalated in a cascade
               "thresholds": {"default": [0.25, 0.75], "grounding": [0.0, 0.5]}, "benefit_of_doubt": ["grounding"]},
}


def est_tokens(obj) -> int:
    """Token estimate: characters of the JSON (or text) / 2.7."""
    s = obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, default=str)
    return int(len(s) / CHARS_PER_TOKEN) + 1


def fits(profile: dict, state, questions: dict) -> bool:
    """Does one request fit the backend's window (minus the safety margin)?"""
    st, qs = est_tokens(state), [est_tokens(q) for q in questions.values()] or [0]
    lim = 1 - SAFETY
    if st > profile["state_tokens"] or st + max(qs) > profile["pass_tokens"] * lim:
        return False
    return profile["per_pass"] or st + sum(qs) <= profile["context_tokens"] * lim


def confidence(answer: dict, kind: str = "jev") -> float:
    """The backend's confidence if it gave one, else: noul |2p-1|; choice/score (K*p_max-1)/(K-1) (Cygnet's formula)."""
    if isinstance(answer.get("confidence"), (int, float)):
        return float(answer["confidence"])
    if answer.get("type") == "noul" or "noul" in answer:
        return abs(2 * float(answer.get("noul", 0.5)) - 1)
    ps = list((answer.get("probabilities") or {}).values())
    k = len(ps)
    return (k * max(ps) - 1) / (k - 1) if k > 1 else 0.0


class SystemOneError(Exception):
    def __init__(self, status: int, message: str, retryable: bool):
        super().__init__(f"System One {status}: {message}")
        self.status, self.message, self.retryable = status, message, retryable


def _error_message(body: bytes) -> str:
    try:
        d = json.loads(body or b"{}")
    except ValueError:
        return (body or b"").decode("utf-8", "replace")[:300]
    e = d.get("error", d.get("detail", d)) if isinstance(d, dict) else d
    if isinstance(e, dict):
        e = e.get("message") or e.get("msg") or json.dumps(e)
    return str(e)[:500]


def _retry_after(headers) -> float | None:
    v = (headers or {}).get("Retry-After") if headers is not None else None
    if not v:
        return None
    try:
        return max(0.0, float(v))
    except ValueError:
        try:
            return max(0.0, parsedate_to_datetime(v).timestamp() - time.time())
        except (TypeError, ValueError):
            return None


_SEMAPHORES: dict[tuple, threading.Semaphore] = {}
_SEM_LOCK = threading.Lock()


class SystemOneClient:
    """`decide(state, questions)` -> {answers, usage {input_tokens, output_tokens, cost}, model, request_id, latency_ms, cached}."""

    def __init__(self, base_url: str, model: str, api_key: str | None = None, timeout: float = 120, retries: int = 4,
                 max_parallel: int = 8, backoff: float = 1.0, usd_per_m_input: float | None = None):
        self.base_url, self.model, self.api_key = base_url.rstrip("/"), model, api_key
        self.timeout, self.retries, self.backoff, self.price = timeout, retries, backoff, usd_per_m_input
        with _SEM_LOCK:
            self.sem = _SEMAPHORES.setdefault((self.base_url, max_parallel), threading.Semaphore(max(1, max_parallel)))

    def cache_key(self, state, questions) -> str:
        return hashlib.sha256(json.dumps([self.base_url, self.model, state, questions], sort_keys=True,
                                         ensure_ascii=False, default=str).encode()).hexdigest()

    def decide(self, state, questions: dict, cache_dir: Path | None = None) -> dict:
        key = self.cache_key(state, questions)
        f = Path(cache_dir) / f"{key}.json" if cache_dir else None
        if f and f.exists():
            try:
                return {**json.loads(f.read_text())["response"], "cached": True, "cache_key": key}
            except (ValueError, KeyError, OSError):
                pass
        req = {"model": self.model, "state": state, "questions": questions}
        out = self._post(req)
        out["cache_key"] = key
        if f:
            f.parent.mkdir(parents=True, exist_ok=True)
            tmp = f.with_suffix(f".{threading.get_ident()}.tmp")
            tmp.write_text(json.dumps({"request": req, "response": out}, indent=1, ensure_ascii=False))
            tmp.replace(f)
        return {**out, "cached": False}

    def _post(self, req: dict) -> dict:
        body = json.dumps(req, ensure_ascii=False).encode()
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        last = None
        for attempt in range(self.retries + 1):
            t0 = time.time()
            try:
                with self.sem:
                    r = urllib.request.urlopen(urllib.request.Request(self.base_url + "/v1/systemone", body, headers, method="POST"),
                                               timeout=self.timeout)
                    data, rid = r.read(), r.headers.get("x-typesafe-request-id")
                return self._normalise(json.loads(data), rid, int((time.time() - t0) * 1000))
            except urllib.error.HTTPError as e:
                status, msg = e.code, _error_message(e.read())
                last = SystemOneError(status, msg, status in RETRYABLE or status >= 500)
                wait = _retry_after(e.headers)
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
                last, wait = SystemOneError(0, f"connection failed: {getattr(e, 'reason', e)}", True), None
            except ValueError as e:
                last, wait = SystemOneError(200, f"response not JSON: {e}", True), None
            if not last.retryable or attempt == self.retries:
                raise last
            time.sleep(wait if wait is not None else self.backoff * 2 ** attempt * (0.5 + random.random()))
        raise last  # pragma: no cover

    def _normalise(self, d: dict, rid: str | None, ms: int) -> dict:
        if not isinstance(d, dict) or not isinstance(d.get("answers"), dict):
            raise SystemOneError(200, f"no answers in response: {str(d)[:200]}", True)
        u = d.get("usage") or {}
        inp = int(u.get("input_tokens", u.get("prompt_tokens")) or 0)
        out = int(u.get("output_tokens", u.get("completion_tokens")) or 0)
        cost = u.get("cost")
        if cost is None:
            cost = inp * self.price / 1e6 if self.price is not None else 0.0
        return {"answers": d["answers"], "usage": {"input_tokens": inp, "output_tokens": out, "cost": float(cost)},
                "model": d.get("model") or self.model, "request_id": rid or d.get("id"), "provider": d.get("provider"),
                "latency_ms": ms}


def resolve_profile(name: str, base_url: str | None = None) -> tuple[str, dict]:
    """The profile, switched to the one whose host matches `base_url` when a jev URL points at OpenRouter / LLM Gateway."""
    if base_url:
        host = urlparse(base_url).netloc
        for n, p in PROFILES.items():
            if n.startswith("jev") and name.startswith("jev") and urlparse(p["base_url"]).netloc == host:
                return n, dict(PROFILES[n])
    return name, dict(PROFILES[name])


class SystemOneJudge(Judge):
    """One class, four registered names (the backend profiles). Options: model, base_url, api_key, precision, thresholds
    ({component: [lo, hi]} or [lo, hi]; env SYSTEMONE_THRESHOLDS as JSON), timeout, retries, max_parallel, backoff."""
    profile_name = "jev"
    accepts_ctx = True

    def __init__(self, model: str | None = None, base_url: str | None = None, api_key: str | None = None,
                 precision: str | None = None, thresholds=None, timeout: float = 120, retries: int = 4,
                 max_parallel: int | None = None, backoff: float = 1.0, **_):
        url = base_url or os.environ.get("SYSTEMONE_BASE_URL")
        self.backend, p = resolve_profile(self.profile_name, url)
        p["base_url"] = url or p["base_url"]
        p["model"] = model or os.environ.get("SYSTEMONE_MODEL") or p["model"]
        if self.backend == "cygnet":
            p["precision"] = precision or os.environ.get("CYGNET_PRECISION") or p["precision"]
        elif precision:
            p["precision"] = precision
        th = dict(p["thresholds"])
        if thresholds is None and os.environ.get("SYSTEMONE_THRESHOLDS"):
            thresholds = json.loads(os.environ["SYSTEMONE_THRESHOLDS"])
        if isinstance(thresholds, (list, tuple)):
            th["default"] = list(thresholds)
        elif isinstance(thresholds, dict):
            th.update(thresholds)
        p["thresholds"] = th
        if os.environ.get("SYSTEMONE_VARIANTS"):  # experiments: decompose.VARIANTS, comma-separated
            p["variants"] = [v.strip() for v in os.environ["SYSTEMONE_VARIANTS"].split(",") if v.strip()]
        self.profile, self.model = p, p["model"]
        self.max_workers = max_parallel or p["concurrency"]
        self.client = SystemOneClient(p["base_url"], p["model"], api_key or os.environ.get(p["key_env"]) or None,
                                      timeout, retries, self.max_workers, backoff, p.get("usd_per_m_input"))

    def judge(self, payload: dict, cache_dir: Path | None = None, **_) -> dict:
        from . import decompose as D
        t0 = time.time()
        plan = D.plan(payload, self.profile)
        cdir = Path(cache_dir) / self.backend if cache_dir else None
        answers, calls, err = {}, [], None

        def one(c):
            return c, self.client.decide(c["state"], c["questions"], cdir)

        def run(batch):
            with ThreadPoolExecutor(max(1, min(len(batch), self.max_workers))) as ex:
                for c, r in ex.map(one, batch):
                    answers.update(r["answers"])
                    calls.append({"qids": list(c["questions"]), "cache_key": r["cache_key"], "cached": r["cached"],
                                  "request_id": r.get("request_id"), "latency_ms": r.get("latency_ms", 0),
                                  "model": r.get("model"), "provider": r.get("provider"), "usage": r["usage"]})
        try:
            run(plan["calls"])
            extra = D.followups(plan, answers, self.profile)   # close choice answers, asked again with the options reversed
            if extra:
                run(extra)
        except SystemOneError as e:
            err = e
        meta = {"backend": self.backend, "model": self.model, "base_url": self.profile["base_url"],
                "model_reported": sorted({c["model"] for c in calls if c.get("model")}),
                "precision": self.profile.get("precision"),
                "cost_usd": round(sum(c["usage"]["cost"] for c in calls if not c["cached"]), 6),
                "duration_ms": int((time.time() - t0) * 1000), "latency_ms": sum(c["latency_ms"] for c in calls if not c["cached"]),
                "request_ids": [c["request_id"] for c in calls if c.get("request_id")],
                "n_questions": sum(len(c["questions"]) for c in plan["calls"]), "n_calls": len(plan["calls"]),
                "cached_calls": sum(c["cached"] for c in calls), "calls": calls,
                "input_tokens": sum(c["usage"]["input_tokens"] for c in calls), "thresholds": self.profile["thresholds"]}
        if err is not None:
            meta["error"] = {"status": err.status, "message": err.message}
            return {"outcome": "judge_failed", "categories": [], "severity": "none", "per_turn": [], "unsupported_claims": [],
                    "actions": [], "confidence": 0.0, "rationale": f"decision backend failed: {err}", "judge": meta}
        v = D.combine(payload, plan, answers, self.profile)
        v["judge"] = {**meta, **v.pop("judge_extra")}
        return v


for _name in PROFILES:
    register(type(f"SystemOneJudge_{_name.replace('-', '_')}", (SystemOneJudge,), {"name": _name, "profile_name": _name}))
