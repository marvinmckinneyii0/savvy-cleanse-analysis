import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Contact from '@/pages/contact';
import Features from '@/pages/features';

/**
 * The concierge beta is a done-for-you service: a person runs SAINT on a
 * customer's CSV and sends back a report. Public pages must not describe
 * things that do not exist yet.
 */
const NOT_OFFERED = [
  /upload your (data|files)/i,
  /\b(json|xlsx|xls|xml|tsv|excel)\b/i,
  /jupyter|notebook/i,
  /python|pandas|numpy|scikit/i,
  /dashboard/i,
  /plots?\b|histograms?|visuali[sz]ations?|interactive/i,
  /predictive|prescriptive|forecast/i,
  /p-values?|confidence intervals?/i,
  /sharing links?|collaborate/i,
  /enterprise|compliance|peer-reviewed|worldwide/i,
  /encrypted/i,
  /signing up|sign in|free trial/i,
  /\bapi\b/i,
  /unstructured/i,
];

const pageText = (page: JSX.Element) =>
  render(<MemoryRouter>{page}</MemoryRouter>).container.textContent ?? '';

beforeEach(() => {
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

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('features page copy for the concierge beta', () => {
  it.each(NOT_OFFERED)('does not mention %s', (pattern) => {
    expect(pageText(<Features />)).not.toMatch(pattern);
  });

  it('describes what the beta delivers and its limits', () => {
    const text = pageText(<Features />);

    expect(text).toMatch(/Cleaning is off unless you ask for it/);
    expect(text).toMatch(/Your original file is never changed/);
    expect(text).toMatch(/Word \(\.docx\)/);
    expect(text).toMatch(/CSV files up to 100 MB/);
    expect(text).toMatch(/Charts are optional and included only when explicitly configured/);
  });
});

describe('contact page copy for the concierge beta', () => {
  it.each(NOT_OFFERED)('does not mention %s', (pattern) => {
    expect(pageText(<Contact />)).not.toMatch(pattern);
  });

  it('answers the questions a beta customer has', () => {
    const text = pageText(<Contact />);

    expect(text).toMatch(/There is no self-serve upload or account yet/);
    expect(text).toMatch(/CSV only, up to 100 MB/);
    expect(text).toMatch(/health records, financial account data or government IDs/);
    expect(text).toMatch(/delete it 7 days after the report is delivered/);
    expect(text).toMatch(/Cleaning is off by default/);
    expect(text).toMatch(/keeps your original file unchanged/);
  });
});
