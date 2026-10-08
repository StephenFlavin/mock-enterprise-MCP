"""`python -m mockmcp eval <step>`: recipe -> run -> grade -> report. Each step lives in its own module with
add_args(parser) and main(args); this file only wires them up."""
import importlib

STEPS = {
    "recipe": ("mockmcp.eval.recipe", "build a run folder from a recipe: tasks, per-task MCP configs, run scripts"),
    "run": ("mockmcp.eval.runner", "run every task of a run folder through a harness (default claude-code), recording tool calls"),
    "grade": ("mockmcp.eval.grade", "deterministic checks + judge for every task in a run folder"),
    "calibrate": ("mockmcp.eval.calibrate", "re-judge a graded run with another judge (decision model / cascade) and measure agreement"),
    "report": ("mockmcp.eval.report", "write report.md (failure categories first) and results.jsonl"),
    "traps": ("mockmcp.eval.traps", "regenerate the trap bank (bench/traps.yaml)"),
}


def add_parser(sub):
    p = sub.add_parser("eval", help="benchmark LLMs on scenarios with n tools loaded (see docs/BENCHMARKING.md)")
    steps = p.add_subparsers(dest="step", required=True)
    for name, (mod, help_) in STEPS.items():
        sp = steps.add_parser(name, help=help_)
        try:
            importlib.import_module(mod).add_args(sp)
        except (ImportError, AttributeError):
            pass  # module not built yet


def main(a):
    return importlib.import_module(STEPS[a.step][0]).main(a)
