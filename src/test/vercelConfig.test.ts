import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const read = (file: string) => readFileSync(resolve(process.cwd(), file), 'utf-8');

interface VercelConfig {
  framework: string;
  buildCommand: string;
  outputDirectory: string;
  rewrites: Array<{ source: string; destination: string }>;
  headers: Array<{ source: string; headers: Array<{ key: string; value: string }> }>;
}

describe('Vercel deployment config', () => {
  const config = JSON.parse(read('vercel.json')) as VercelConfig;

  it('builds the Vite app into dist', () => {
    expect(config.framework).toBe('vite');
    expect(config.buildCommand).toBe('npm run build');
    expect(config.outputDirectory).toBe('dist');
  });

  it('serves index.html for every route so client-side links work on reload', () => {
    expect(config.rewrites).toEqual([{ source: '/(.*)', destination: '/index.html' }]);
  });

  it('sends basic security headers on every page', () => {
    const all = config.headers.find((rule) => rule.source === '/(.*)');
    const keys = all?.headers.map((header) => header.key) ?? [];

    expect(keys).toEqual(
      expect.arrayContaining(['X-Content-Type-Options', 'X-Frame-Options', 'Referrer-Policy']),
    );
  });

  it('keeps secrets and the Python pipeline out of the upload', () => {
    const ignored = read('.vercelignore')
      .split(/\r?\n/)
      .map((line) => line.trim());

    for (const entry of ['.env', 'backend/', '.venv/', '_bmad-output/']) {
      expect(ignored).toContain(entry);
    }
  });
});
