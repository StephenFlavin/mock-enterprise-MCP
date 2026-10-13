// Build-time inputs that come from the repo rather than from site/: the palette, the reference docs, the examples.
// Each step is its own script so it can be run and checked alone.
import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';

const python = process.env.PYTHON || 'python3';
const steps = [
  [python, ['scripts/tokens.py']],
  ['node', ['scripts/sync-docs.mjs']],
  [python, ['-I', 'scripts/prepare_examples.py']],
];
for (const [cmd, args] of steps) {
  if (!existsSync(args.at(-1))) { console.log(`skip ${args.at(-1)} (not written yet)`); continue; }
  execFileSync(cmd, args, { stdio: 'inherit' });
}
