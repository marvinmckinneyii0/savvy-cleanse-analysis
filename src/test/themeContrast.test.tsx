import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import AnalysisTypes from '@/components/AnalysisTypes';
import Features from '@/components/Features';
import Hero from '@/components/Hero';
import { LEAD_FALLBACK_EMAIL } from '@/lib/leadCapture';
import About from '@/pages/about';
import Contact from '@/pages/contact';
import FeaturesPage from '@/pages/features';
import NotFound from '@/pages/NotFound';
import Privacy from '@/pages/privacy';
import SavvyAnalytics from '@/pages/savvy-analytics';
import Terms from '@/pages/terms';

/**
 * Every page follows the home page's design (owner instruction, 2026-11-11):
 * the same hero treatment, the same white bands, the same closing band.
 *
 * The home page keeps its light bands white in dark mode, which is the site's
 * default. Text placed straight on a white band would inherit the dark theme's
 * near-white colour and vanish, so each white band carries `light-surface`
 * (src/index.css), which gives it the light theme's text colours.
 *
 * The price section and price page are owner-only and are not covered here.
 */
const HOME_HERO = 'py-20 md:py-28 bg-gradient-to-b from-savvy-white to-savvy-gold/5';
const HOME_H1 = 'text-3xl md:text-5xl font-bold tracking-tighter';
const HOME_CLOSING_BAND = 'py-16 bg-gradient-to-r from-savvy-dark to-savvy-midnight';

type Surface = [string, JSX.Element];

const INNER_PAGES: Surface[] = [
  ['features page', <FeaturesPage />],
  ['about page', <About />],
  ['contact page', <Contact />],
  ['savvy analytics page', <SavvyAnalytics />],
];

const WHITE_BAND_SURFACES: Surface[] = [
  ['home features', <Features />],
  ['home analysis', <AnalysisTypes />],
  ...INNER_PAGES,
  ['privacy page', <Privacy />],
  ['terms page', <Terms />],
];

const renderSurface = (element: JSX.Element) =>
  render(<MemoryRouter>{element}</MemoryRouter>).container;

const isWhiteBand = (classes: string) => /(^|\s)bg-(white|savvy-white)(\s|$)/.test(classes);

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
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

describe('the home page keeps its original design', () => {
  it('the hero uses the original gradient with no dark-mode override', () => {
    const section = renderSurface(<Hero />).querySelector('section') as HTMLElement;

    expect(section.className).toBe(HOME_HERO);
    expect(section.querySelector('h1')?.className).toBe(HOME_H1);
  });

  it('the feature and analysis bands stay white in dark mode', () => {
    for (const element of [<Features />, <AnalysisTypes />]) {
      const section = renderSurface(element).querySelector('section') as HTMLElement;

      expect(isWhiteBand(section.className)).toBe(true);
      expect(section.className).not.toMatch(/dark:/);
    }
  });
});

describe('home text fixes that leave the design alone', () => {
  it('the formula lines in the analysis tiles have a dark-mode text colour', () => {
    const formulas = renderSurface(<AnalysisTypes />).querySelectorAll('code.formula');

    // Navy text on the tile's dark formula strip was 1.14:1 in dark mode.
    expect(formulas.length).toBeGreaterThan(0);
    for (const formula of formulas) {
      expect(formula.className).toContain('dark:text-foreground');
    }
  });
});

describe('every other page matches the home page', () => {
  it.each(INNER_PAGES)('%s: opens with the home page hero', (_name, element) => {
    const hero = renderSurface(element).querySelector('main > section') as HTMLElement;

    expect(hero.className).toBe(HOME_HERO);
    expect(hero.querySelector('h1')?.className).toContain(HOME_H1);
  });

  it.each([
    ['about page', <About />],
    ['contact page', <Contact />],
    ['savvy analytics page', <SavvyAnalytics />],
  ] as Surface[])('%s: closes with the home page band', (_name, element) => {
    const sections = renderSurface(element).querySelectorAll('main > section');

    expect(sections[sections.length - 1].className).toContain(HOME_CLOSING_BAND);
  });

  it.each(INNER_PAGES)('%s: has no navy hero and no grey-on-dark text', (_name, element) => {
    const html = renderSurface(element).innerHTML;

    expect(html).not.toContain('via-savvy-midnight');
    expect(html).not.toMatch(/text-gray-\d+/);
  });

  it('the features page uses the home page card, not a translucent one', () => {
    const html = renderSurface(<FeaturesPage />).innerHTML;

    // A half-transparent card on a white band turns grey and its text fades.
    expect(html).not.toMatch(/bg-card\/\d+|backdrop-blur/);
    expect(html).toContain('shadow-sm hover:shadow-md transition-shadow');
  });

  it('the not-found page uses theme colours, not fixed greys and blues', () => {
    const html = renderSurface(<NotFound />).innerHTML;

    expect(html).not.toMatch(/bg-gray-\d+|text-gray-\d+|text-blue-\d+/);
  });
});

describe('text on white bands stays readable in dark mode', () => {
  it.each(WHITE_BAND_SURFACES)('%s: each white band is a light surface', (_name, element) => {
    const container = renderSurface(element);
    const whiteBands = [...container.querySelectorAll('section')].filter((section) =>
      isWhiteBand(section.className),
    );

    expect(whiteBands.length).toBeGreaterThan(0);
    for (const band of whiteBands) {
      expect(band.className).toMatch(/(^|\s)light-surface(\s|$)/);
      expect(band.className).not.toMatch(/dark:bg-/);
    }
  });

  it('light-surface sets dark text on the band and restores light text inside dark cards', () => {
    const css = readFileSync(resolve(process.cwd(), 'src/index.css'), 'utf-8');
    const band = css.match(/\.dark \.light-surface \{([^}]*)\}/)?.[1] ?? '';
    const cards = css.match(/\.dark \.light-surface \.bg-card,[^{]*\{([^}]*)\}/)?.[1] ?? '';

    // Light theme foreground on the band...
    expect(band).toContain('--foreground: 222.2 84% 4.9%');
    expect(band).toContain('--muted-foreground: 215.4 16.3% 46.9%');
    // ...dark theme foreground again inside cards and other dark panels.
    expect(cards).toContain('--foreground: 210 40% 98%');
    expect(cards).toContain('--muted-foreground: 215 20.2% 65.1%');
  });

  it.each([
    ['about page', <About />],
    ['savvy analytics page', <SavvyAnalytics />],
  ] as Surface[])('%s: white outline buttons on the closing band stay transparent', (_name, element) => {
    const container = renderSurface(element);
    const whiteOutline = [...container.querySelectorAll('button, a')].filter((el) =>
      /(^|\s)border-white(\s|$)/.test(el.className),
    );

    // The outline variant paints the page background, which is white in light
    // mode: white text on a white button.
    expect(whiteOutline.length).toBeGreaterThan(0);
    for (const el of whiteOutline) {
      expect(el.className).toMatch(/(^|\s)bg-transparent(\s|$)/);
    }
  });
});

describe('contact details', () => {
  it('uses the savvyanalytics.co address everywhere', () => {
    expect(LEAD_FALLBACK_EMAIL).toBe('info@savvyanalytics.co');

    for (const element of [<Contact />, <About />, <Privacy />, <Terms />, <SavvyAnalytics />]) {
      const container = renderSurface(element);
      const text = container.textContent ?? '';
      const hrefs = [...container.querySelectorAll('a')].map((a) => a.getAttribute('href') ?? '');

      expect(text).not.toContain('savvyanalytics.info');
      expect(hrefs.join(' ')).not.toContain('savvyanalytics.info');
      expect(text).toContain('info@savvyanalytics.co');
    }
  });

  it('the contact page says SAINT supports businesses globally', () => {
    const text = renderSurface(<Contact />).textContent ?? '';

    expect(text).toContain('Supporting businesses globally');
    expect(text).not.toContain('nationwide');
  });

  it('the home headline promises a report on your data, not only CSV', () => {
    const h1 = renderSurface(<Hero />).querySelector('h1')?.textContent ?? '';

    expect(h1).toBe('A Data-Quality Report on Your Data, Done for You');
  });

  it('gives Dallas, not Lisbon, as the location', () => {
    for (const element of [<Contact />, <About />]) {
      const text = renderSurface(element).textContent ?? '';

      expect(text).toContain('Dallas, Texas');
      expect(text).not.toContain('Lisbon');
    }
  });
});
