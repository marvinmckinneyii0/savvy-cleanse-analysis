import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import SavvyAnalytics from '@/pages/savvy-analytics';

const renderPage = () =>
  render(
    <MemoryRouter>
      <SavvyAnalytics />
    </MemoryRouter>,
  );

const main = () => screen.getByRole('main');

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

describe('Savvy Analytics page', () => {
  it('lists the three services named on savvyanalytics.co', () => {
    renderPage();
    const services = document.getElementById('services') as HTMLElement;

    expect(within(services).getByRole('heading', { name: 'Our Services' })).toBeInTheDocument();
    for (const name of [
      'AI Strategy & Roadmaps',
      'Business Solutions & Automation',
      'Custom Software & AI Implementation',
    ]) {
      expect(within(services).getByText(name)).toBeInTheDocument();
    }
  });

  it('no longer shows the services, offices and figures that the company site does not', () => {
    renderPage();
    const text = main().textContent ?? '';

    for (const gone of [
      'AI Strategy Consulting',
      'Process Automation',
      'Industries We Serve',
      'Global Presence',
      'Europe',
      'Lisbon',
      'London',
      'New York',
      'Projects Delivered',
      'Enterprise Clients',
      'Client Retention',
      'savvyanalytics.info',
    ]) {
      expect(text).not.toContain(gone);
    }
  });

  it('points to the savvyanalytics.co site, services and booking pages', () => {
    renderPage();
    const hrefs = within(main())
      .getAllByRole('link')
      .map((link) => link.getAttribute('href'));

    expect(hrefs).toContain('https://www.savvyanalytics.co');
    expect(hrefs).toContain('https://www.savvyanalytics.co/services');
    expect(hrefs).toContain('https://www.savvyanalytics.co/book-online');
    expect(hrefs).toContain('mailto:info@savvyanalytics.co');
    expect(hrefs).toContain('/contact');
  });

  it('has no button that does nothing', () => {
    renderPage();

    // Every call to action is a real link; there are no bare buttons in the page body.
    expect(within(main()).queryAllByRole('button')).toHaveLength(0);
    for (const link of within(main()).getAllByRole('link')) {
      expect(link.getAttribute('href')).toBeTruthy();
      expect(link.getAttribute('href')).not.toBe('#');
    }
  });

  it('opens external links in a new tab without leaking the opener', () => {
    renderPage();
    const external = within(main())
      .getAllByRole('link')
      .filter((link) => link.getAttribute('href')?.startsWith('https://'));

    expect(external.length).toBeGreaterThan(0);
    for (const link of external) {
      expect(link).toHaveAttribute('target', '_blank');
      expect(link.getAttribute('rel')).toContain('noopener');
    }
  });

  it('uses the home page section styles', () => {
    renderPage();
    const sectionClasses = [...main().querySelectorAll(':scope > section')].map(
      (section) => section.className,
    );

    // Hero and closing section match src/components/Hero.tsx and CTA.tsx.
    expect(sectionClasses[0]).toContain('py-20 md:py-28 bg-gradient-to-b from-savvy-white to-savvy-gold/5');
    expect(sectionClasses.at(-1)).toBe('py-16 bg-gradient-to-r from-savvy-dark to-savvy-midnight');
    // No section keeps the old dark-hero or blue-gradient treatments.
    for (const classes of sectionClasses) {
      expect(classes).not.toContain('via-savvy-midnight');
      expect(classes).not.toContain('savvy-blue');
    }
    expect(main().innerHTML).not.toContain('savvy-blue');
  });

  it('gives every light section a dark-mode background', () => {
    renderPage();

    // The site defaults to dark mode, where headings are near-white. A section
    // that stays white there hides its own heading.
    for (const section of main().querySelectorAll(':scope > section')) {
      const classes = section.className;
      if (/(^|\s)bg-(white|savvy-white)(\s|$)|from-savvy-white/.test(classes)) {
        expect(classes).toMatch(/dark:/);
      }
    }
  });
});
