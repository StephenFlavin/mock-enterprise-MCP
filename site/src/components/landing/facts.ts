// Build-time facts the landing page needs that src/data/examples.json does not hold: the per-task outcome bands of one
// run at one budget (the hero's "every task, one square"), the task mix, and the repo's system and tool counts.
// Read from the repo at build time; nothing here types a figure by hand.
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { gunzipSync } from 'node:zlib';

/** The repo root: the build and `astro check` both run from site/. */
const ROOT = resolve(process.cwd(), '..');
if (!existsSync(join(ROOT, 'docs/examples'))) throw new Error(`landing/facts: no docs/examples under ${ROOT}; run from site/`);

interface Task { task_id: string; run: string; kind: string; band: string; band_rank: number; trap: { type: string } | null }
interface Report { runs: { run: string; bands: Record<string, number> }[]; tasks: Task[] }

const cache = new Map<string, Report>();
/** docs/examples/<name>/report.json.gz, parsed once per build. */
export function report(name: string): Report {
  if (!cache.has(name)) cache.set(name, JSON.parse(gunzipSync(readFileSync(join(ROOT, 'docs/examples', name, 'report.json.gz'))).toString('utf8')));
  return cache.get(name)!;
}

/** Bands from best to worst, as the report's waffle orders them (band_rank 7 … 0). */
export const BAND_ORDER = ['pass', 'honest_fail', 'partial', 'over_cautious', 'fabricated', 'unsafe_benign', 'unsafe_reversible', 'unsafe_external'] as const;
export const BAND_LABEL: Record<string, string> = {
  pass: 'pass', honest_fail: 'honest fail', partial: 'partial', over_cautious: 'over-cautious', fabricated: 'fabricated',
  unsafe_benign: 'unsafe: draft or note', unsafe_reversible: 'unsafe: reversible', unsafe_external: 'unsafe: external',
};

/** One run's tasks at one budget, best band first, with that budget's band counts (report runs[].bands). */
export function waffle(name: string, budget: string) {
  const r = report(name);
  const tasks = r.tasks.filter((t) => t.run === budget).sort((a, b) => b.band_rank - a.band_rank)
    .map((t) => ({ id: t.task_id, band: t.band }));
  const bands = r.runs.find((x) => x.run === budget)?.bands;
  if (!tasks.length || !bands) throw new Error(`landing/facts: no tasks for ${name} at ${budget}`);
  return { tasks, bands: BAND_ORDER.filter((b) => bands[b]).map((b) => ({ band: b, label: BAND_LABEL[b], n: bands[b] })) };
}

/** Task counts by kind and trap counts by type over a whole run, most common trap first. */
export function taskMix(name: string) {
  const count = (xs: string[]) => xs.reduce<Record<string, number>>((m, x) => ((m[x] = (m[x] ?? 0) + 1), m), {});
  const tasks = report(name).tasks;
  const traps = count(tasks.flatMap((t) => (t.trap ? [t.trap.type] : [])));
  return { kinds: count(tasks.map((t) => t.kind)), traps: Object.entries(traps).sort((a, b) => b[1] - a[1]) };
}

/** Systems: folders under systems/ with a system.yaml, not shared (`_master`). Tools: README's "about N tools". */
export function repo() {
  const systems = readdirSync(join(ROOT, 'systems'), { withFileTypes: true })
    .filter((d) => d.isDirectory() && !d.name.startsWith('_') && existsSync(join(ROOT, 'systems', d.name, 'system.yaml')));
  const tools = readFileSync(join(ROOT, 'README.md'), 'utf8').match(/about ([\d,]+) tools/)?.[1];
  if (!tools) throw new Error('landing/facts: README.md no longer says "about N tools"');
  return { systems: systems.length, tools };
}

/** A short label for a system from the `name:` in its system.yaml: the acronym in brackets ("… (WMS)"), a leading
 * acronym ("ERP (General Ledger)"), or the name without a trailing " System". The full name goes in a tooltip. */
export function systemLabel(id: string) {
  const name = readFileSync(join(ROOT, 'systems', id, 'system.yaml'), 'utf8').match(/^name:\s*(.+)$/m)?.[1].trim();
  if (!name) throw new Error(`landing/facts: systems/${id}/system.yaml has no name`);
  const short = name.match(/\(([A-Z]{2,})\)$/)?.[1] ?? name.match(/^([A-Z]{2,})\b/)?.[1] ?? name.replace(/ System$/, '');
  return { id, name, short };
}
