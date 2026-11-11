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
    expect(text).toMatch(/2026\s*SAINT Launch|SAINT Launch/);
    expect(text).not.toContain('10K+ Users');
    expect(text).not.toContain('API Release');
    expect(text).not.toContain('50+ countries');
  });

  it('drops the users and countries figures and keeps the other two', () => {
    const text = aboutText();

    expect(text).not.toContain('Active Users');
    expect(text).not.toContain('Countries');
    expect(text).toContain('Rows Processed');
    expect(text).toContain('Uptime');
  });
});
