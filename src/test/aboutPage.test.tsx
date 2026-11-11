import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import About from '@/pages/about';

const aboutText = () =>
  render(
    <MemoryRouter>
      <About />
    </MemoryRouter>,
  ).container.textContent ?? '';

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

describe('About page content (owner update, 2026-11-11)', () => {
  it('shows Marvin McKinney as the only team member', () => {
    const text = aboutText();

    expect(text).toContain('Marvin McKinney');
    expect(text).toContain('CEO & Founder');
    expect(text).toContain(
      'Former data science leader at Fortune 500 companies. Passionate about democratizing analytics.',
    );
    for (const removed of ['Sarah Rodriguez', 'Marcus Chen', 'Elena Vasquez', 'Stanford', 'Ex-Google', 'Netflix']) {
      expect(text).not.toContain(removed);
    }
  });

  it('keeps only the founding and SAINT launch milestones', () => {
    const text = aboutText();

    expect(text).toContain('Company Founded');
    expect(text).toMatch(/2026\s*SAINT Concierge Beta/);
    expect(text).toContain('Preparing a guided beta');
    expect(text).not.toContain('Released our first product');
    expect(text).not.toContain('SAINT Launch');
    expect(text).not.toContain('10K+ Users');
    expect(text).not.toContain('API Release');
    expect(text).not.toContain('50+ countries');
  });

  it('removes unverified numerical claims and obsolete user statistics', () => {
    const text = aboutText();

    for (const unsupported of [
      'Active Users', 'Countries', 'Rows Processed', 'Uptime',
      '500M+', '99.9%', '10K+', '50+',
    ]) {
      expect(text).not.toContain(unsupported);
    }
  });

  it('routes the beta request to contact and provides a working email action', () => {
    const { getByRole, queryByRole } = render(
      <MemoryRouter><About /></MemoryRouter>,
    );

    expect(getByRole('link', { name: 'Request a Data-Quality Report' }).getAttribute('href'))
      .toBe('/contact');
    expect(getByRole('link', { name: 'Email Our Team' }).getAttribute('href'))
      .toBe('mailto:info@savvyanalytics.co');
    expect(queryByRole('button', { name: 'Start Free Trial' })).toBeNull();
  });
});
