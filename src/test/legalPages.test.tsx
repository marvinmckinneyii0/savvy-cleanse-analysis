import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { beforeAll, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '@/App';
import Footer from '@/components/layout/Footer';

const renderAt = (path: string) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );

const mainText = () => document.querySelector('main')?.textContent ?? '';

beforeAll(() => {
  // jsdom has no matchMedia; the theme provider and toasters query it.
  vi.stubGlobal(
    'matchMedia',
    vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  );
});

describe('privacy policy page', () => {
  it('is routed and marked as a draft', () => {
    renderAt('/privacy');

    expect(screen.getByRole('heading', { level: 1, name: 'Privacy Policy' })).toBeInTheDocument();
    expect(screen.getByRole('note')).toHaveTextContent('This page is a draft');
  });

  it('states the data-handling commitments', () => {
    renderAt('/privacy');
    const text = mainText();

    expect(text).toMatch(/delete your file, and any cleaned copy we made, 7 days after we deliver your report/);
    expect(text).toMatch(/health records, financial account data or government ID numbers/);
    expect(text).toMatch(/We do not sell your data/);
  });

  it('discloses every outside service that receives data', () => {
    renderAt('/privacy');
    const text = mainText();

    expect(text).toMatch(/Formspree/);
    expect(text).toMatch(/Anthropic/);
    expect(text).toMatch(/OpenAI or Google/);
    expect(text).toMatch(/some values taken from the file/);
    expect(text).toMatch(/Your whole file is not sent/);
    expect(text).toMatch(/Google Fonts/);
  });
});

describe('terms page', () => {
  it('is routed and marked as a draft', () => {
    renderAt('/terms');

    expect(screen.getByRole('heading', { level: 1, name: 'Terms of Use' })).toBeInTheDocument();
    expect(screen.getByRole('note')).toHaveTextContent('This page is a draft');
  });

  it('states the limits of the service and the report', () => {
    renderAt('/terms');
    const text = mainText();

    expect(text).toMatch(/CSV files of up to 100 MB/);
    expect(text).toMatch(/There is no account and no upload on this site/);
    expect(text).toMatch(/We clean your data only if you ask us to/);
    expect(text).toMatch(/written by AI/);
    expect(text).toMatch(/we cannot produce a report from it/);
  });

  it('states no price', () => {
    renderAt('/terms');

    expect(mainText()).not.toMatch(/\$|\bfree\b|\bfee\b|\bpaid\b|per month/i);
  });
});

describe('legal links and third-party scripts', () => {
  it('the footer links to the terms and privacy pages and has no dead links', () => {
    render(
      <MemoryRouter>
        <Footer />
      </MemoryRouter>,
    );
    const targets = screen.getAllByRole('link').map((link) => link.getAttribute('href'));

    expect(targets).toContain('/terms');
    expect(targets).toContain('/privacy');
    expect(targets).not.toContain('#');
  });

  it('index.html loads no script from a third-party host', () => {
    const html = readFileSync(resolve(process.cwd(), 'index.html'), 'utf-8');
    const scriptSources = [...html.matchAll(/<script[^>]*\ssrc="([^"]+)"/g)].map((m) => m[1]);

    expect(scriptSources).toEqual(['/src/main.tsx']);
  });
});
