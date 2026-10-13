// Copy the repo's long-form guides into the site as the Reference section.
// The repo files stay the single source: this folder is wiped and rewritten on every build (git-ignored).
// Run from anywhere: `node scripts/sync-docs.mjs`; `npm run prepare-site` calls it.
import { existsSync, mkdirSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join, posix } from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO = 'https://github.com/StephenFlavin/mock-enterprise-MCP';
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const OUT = join(ROOT, 'site', 'src', 'content', 'docs', 'reference');

// Source (repo-relative) -> page slug under /reference/, in sidebar order.
const PAGES = [
  { src: 'docs/BENCHMARKING.md', slug: 'benchmarking',
    description: 'The full benchmark guide: recipes, run folders, grading, reports, comparisons and how to evaluate a model.' },
  { src: 'docs/BUILDING_A_SYSTEM.md', slug: 'building-a-system',
    description: 'The contract for building one mock enterprise system: one MCP server from YAML, a generator and seed rows.' },
  { src: 'bench/AUTHORING.md', slug: 'authoring-cases',
    description: 'How to write and validate the ground-truth cases the benchmark grades against.' },
];
const BY_SRC = new Map(PAGES.map((p) => [p.src, p]));

// Markup that may stay as HTML. Every other `<` outside code is escaped, because the guides use `<id>`, `<table>`
// and the like as placeholders in prose; a bare `<table>` there means the word, not the element.
const HTML_OK = /^(<\/?(br|hr|details|summary|sub|sup|kbd)\s*\/?>|<(a|img)\s[^>]*>|<\/a>|<!--|<https?:\/\/[^>\s]+>)/i;

/** Map a link target in `fromSrc` to its place on the site, or on GitHub when the site has no page for it. */
export function rewriteTarget(target, fromSrc, { image = false } = {}) {
  if (/^[a-z][a-z0-9+.-]*:/i.test(target) || target.startsWith('#') || target.startsWith('//')) return target;
  const m = target.match(/^([^?#]*)([?#].*)?$/);
  const [path, rest = ''] = [m[1], m[2]];
  if (!path) return target;
  const resolved = posix.normalize(path.startsWith('/') ? path.slice(1) : posix.join(posix.dirname(fromSrc), path))
    .replace(/\/$/, '');
  if (resolved.startsWith('..')) { console.warn(`sync-docs: ${fromSrc}: link outside the repo left as is: ${target}`); return target; }
  const page = BY_SRC.get(resolved);
  if (page) return `../${page.slug}/${rest}`;
  const ex = resolved.match(/^docs\/examples(?:\/(.*))?$/);
  if (ex) {
    const sub = (ex[1] || '').replace(/(^|\/)README\.md$/, '');
    if (!sub) return `../../examples/${rest}`;
    return `../../examples/${sub}${sub.includes('.') ? '' : '/'}${rest}`;
  }
  if (image) return `https://raw.githubusercontent.com/StephenFlavin/mock-enterprise-MCP/main/${resolved}`;
  const abs = join(ROOT, resolved);
  const kind = existsSync(abs) && statSync(abs).isDirectory() ? 'tree' : 'blob';
  if (!existsSync(abs)) console.warn(`sync-docs: ${fromSrc}: link to a missing repo path: ${target}`);
  return `${REPO}/${kind}/main/${resolved}${rest}`;
}

/** Rewrite links and stray `<` in one line of prose (code spans are left exactly as they are). */
function proseLine(line, fromSrc) {
  // Park code spans behind placeholders so nothing below touches their text.
  const spans = [];
  let s = line.replace(/`+[^`]*`+/g, (m) => `\u0000${spans.push(m) - 1}\u0000`);
  s = s.replace(/(!?)\[([^\]]*)\]\(\s*(<[^>]*>|[^\s)]+)(\s+"[^"]*")?\s*\)/g, (_, bang, text, tgt, title = '') => {
    const bare = tgt.startsWith('<') ? tgt.slice(1, -1) : tgt;
    return `${bang}[${text}](${rewriteTarget(bare, fromSrc, { image: !!bang })}${title})`;
  });
  s = s.replace(/^(\s*\[[^\]]+\]:\s*)(\S+)/, (_, head, tgt) => head + rewriteTarget(tgt, fromSrc));
  s = s.replace(/<(?=[A-Za-z/!])/g, (lt, off, str) => {
    const rest = str.slice(off);
    return HTML_OK.test(rest) ? lt : '&lt;';
  });
  // A code span that names another synced guide becomes a link to its page, unless it is already link text.
  return s.replace(/\u0000(\d+)\u0000/g, (_, i, off, str) => {
    const code = spans[i];
    const name = code.replace(/^`+|`+$/g, '');
    if (!BY_SRC.has(name) || name === fromSrc || str[off - 1] === '[') return code;
    return `[${code}](../${BY_SRC.get(name).slug}/)`;
  });
}

/** Turn one repo guide into a Starlight page: frontmatter from its H1, links rewritten, code untouched. */
export function convert(text, page, order) {
  const lines = text.replace(/\r\n?/g, '\n').split('\n');
  let title = null;
  const out = [];
  let fence = null;
  for (const line of lines) {
    const f = line.match(/^\s*(`{3,}|~{3,})/);
    if (fence) {
      out.push(line);
      if (f && f[1][0] === fence[0] && f[1].length >= fence.length && !line.trim().slice(f[1].length).trim()) fence = null;
      continue;
    }
    if (f) { fence = f[1]; out.push(line); continue; }
    if (title === null) {
      const h = line.match(/^#\s+(.+?)\s*#*\s*$/);
      if (h) { title = h[1].replace(/`/g, ''); continue; }
    }
    out.push(proseLine(line, page.src));
  }
  if (title === null) throw new Error(`sync-docs: ${page.src} has no H1 to take the title from`);
  while (out.length && !out[0].trim()) out.shift();
  while (out.length && !out.at(-1).trim()) out.pop();
  const front = [
    '---',
    `title: ${JSON.stringify(title)}`,
    `description: ${JSON.stringify(page.description)}`,
    `editUrl: ${JSON.stringify(`${REPO}/edit/main/${page.src}`)}`,
    'sidebar:',
    `  order: ${order}`,
    '---',
    '',
    `<!-- Generated from ${page.src} by site/scripts/sync-docs.mjs. Edit the source file, not this one. -->`,
    '',
  ];
  return front.join('\n') + '\n' + out.join('\n') + '\n';
}

function main() {
  rmSync(OUT, { recursive: true, force: true });
  mkdirSync(OUT, { recursive: true });
  PAGES.forEach((page, i) => {
    const text = readFileSync(join(ROOT, page.src), 'utf8');
    writeFileSync(join(OUT, `${page.slug}.md`), convert(text, page, i + 1));
  });
  console.log(`sync-docs: wrote ${PAGES.length} reference pages to site/src/content/docs/reference/`);
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) main();
