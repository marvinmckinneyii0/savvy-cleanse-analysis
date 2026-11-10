import { beforeAll, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '@/App';
import Footer from '@/components/layout/Footer';
import Navbar from '@/components/layout/Navbar';

// Pages hidden for the concierge beta (launch decision D8).
const HIDDEN_PATHS = [
  '/api',
  '/api-reference',
  '/testimonials',
  '/careers',
  '/blog',
  '/documentation',
  '/guides',
];
const HIDDEN_LINK_TARGETS = [...HIDDEN_PATHS, '/dashboard'];

const renderAt = (path: string) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );

const linkTargets = () =>
  screen.getAllByRole('link').map((link) => link.getAttribute('href'));

beforeAll(() => {
  // jsdom has no matchMedia; the theme provider and toasters query it.
  vi.stubGlobal(
    'matchMedia',
    vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  );
  // NotFound logs the missing path on purpose; keep test output readable.
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

describe('pages hidden for the concierge beta', () => {
  it.each(HIDDEN_PATHS)('%s shows the not-found page', (path) => {
    renderAt(path);

    expect(screen.getByRole('heading', { name: '404' })).toBeInTheDocument();
  });

  it('/dashboard redirects to the contact form', () => {
    renderAt('/dashboard');

    expect(document.querySelector('[data-page="contact"]')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Send Message' })).toBeInTheDocument();
  });

  it('still serves a page that stays public', () => {
    renderAt('/contact');

    expect(document.querySelector('[data-page="contact"]')).toBeInTheDocument();
  });

  it('the footer links to none of the hidden pages', () => {
    render(
      <MemoryRouter>
        <Footer />
      </MemoryRouter>,
    );

    for (const target of HIDDEN_LINK_TARGETS) {
      expect(linkTargets()).not.toContain(target);
    }
  });

  it('the navbar links to none of the hidden pages', () => {
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>,
    );

    for (const target of HIDDEN_LINK_TARGETS) {
      expect(linkTargets()).not.toContain(target);
    }
  });

  it('the home page omits the sample-chart and feedback sections', () => {
    renderAt('/');

    expect(screen.getByRole('heading', { name: 'Key Features' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Business Intelligence' })).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'We Value Your Feedback' })).not.toBeInTheDocument();
    expect(document.getElementById('business-intelligence')).not.toBeInTheDocument();
  });
});
