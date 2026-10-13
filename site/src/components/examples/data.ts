// The example figures: src/data/examples.json (written by scripts/prepare_examples.py at build time), or the committed
// sample when the build step has not run yet. Nothing here types a number by hand.
import sample from '../../data/examples.sample.json';

const built = import.meta.glob('../../data/examples.json', { eager: true, import: 'default' });
export type Examples = typeof sample;
export const data = (Object.values(built)[0] ?? sample) as Examples;

export type RunName = keyof Examples['runs'];
export type PairName = keyof Examples['comparisons'];
export type Outcome = keyof Examples['runs'][RunName]['outcomes'];

/** A path under the site's base (e.g. `examples/haiku/report.html`) as an absolute URL path. */
export const href = (path: string) => `${import.meta.env.BASE_URL.replace(/\/$/, '')}/${path}`;

export const pct = (x: number, digits = 1) => `${(100 * x).toFixed(digits)}%`;
export const pts = (d: number) => `${d > 0 ? '+' : d < 0 ? '−' : '±'}${Math.abs(100 * d).toFixed(1)} pts`;
export const usd = (x: number) => `$${x.toFixed(x < 1 ? 3 : 2)}`;
export const ratio = (x: number) => `${x.toFixed(2)}×`;
export const pval = (p: number) => (p < 0.001 ? '< 0.001' : String(Number(p.toPrecision(3))));
export const mb = (bytes: number) => (bytes < 1e6 ? `${Math.round(bytes / 1e3)} kB` : `${(bytes / 1e6).toFixed(1)} MB`);
export const int = (n: number) => n.toLocaleString('en-GB');
export const outcomeLabel = (o: string) => o.replace(/_/g, ' ');
export const budgetLabel = (key: string) => data.budgets.find((b) => b.key === key)?.label ?? key;

/** The budgets in ladder order, with the first and last for "from … to …" sentences. */
export const budgetKeys = data.budgets.map((b) => b.key);
export const first = budgetKeys[0], last = budgetKeys[budgetKeys.length - 1];

/** The highest and lowest value of a per-budget figure, each with the label(s) of the budget(s) that reach it. */
export function extremes(by: Record<string, number>) {
  const vals = budgetKeys.map((k) => by[k]);
  const at = (v: number) => ({ v, label: budgetKeys.filter((k) => by[k] === v).map(budgetLabel).join(' and ') });
  return { high: at(Math.max(...vals)), low: at(Math.min(...vals)) };
}

/** Comparison rows by kind whose McNemar p is under 0.05. */
export const significant = (name: PairName) => data.comparisons[name].by_kind.filter((r) => r.p < 0.05);
