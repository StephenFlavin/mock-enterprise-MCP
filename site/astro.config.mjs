// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

const repo = 'https://github.com/StephenFlavin/mock-enterprise-MCP';

export default defineConfig({
  site: 'https://stephenflavin.github.io',
  base: '/mock-enterprise-MCP',
  trailingSlash: 'ignore',
  integrations: [
    starlight({
      title: 'mock-enterprise-MCP Benchmark',
      description: '96 mock enterprise MCP servers and a benchmark of how well models find their way through their tools.',
      social: [{ icon: 'github', label: 'GitHub', href: repo }],
      editLink: { baseUrl: `${repo}/edit/main/site/` },
      customCss: ['./src/styles/mm-tokens.css', './src/styles/theme.css'],
      // the 3×3 outcome-square mark, as on the landing page (package A)
      logo: { light: './src/components/landing/logo-light.svg', dark: './src/components/landing/logo-dark.svg' },
      favicon: '/favicon.svg',
      sidebar: [
        { label: 'Get started', items: [{ autogenerate: { directory: 'get-started' } }] },
        { label: 'Examples', items: [{ autogenerate: { directory: 'examples' } }] },
        { label: 'Reference', items: [{ autogenerate: { directory: 'reference' } }] },
      ],
    }),
  ],
});
