import React from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import HomePricing from '@/components/Pricing';
import PricingPage from '@/pages/pricing';
import Contact from '@/pages/contact';
import { CONCIERGE_OFFERS, FUTURE_PLANS, offerRequestSubject } from '@/lib/conciergePricing';

const renderWithRouter = (node: React.ReactNode, route = '/') =>
  render(<MemoryRouter initialEntries={[route]}>{node}</MemoryRouter>);

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

describe('SAINT concierge beta pricing consistency', () => {
  it('uses the approved prices with stable offer identifiers', () => {
    expect(CONCIERGE_OFFERS.map((offer) => [offer.id, offer.price])).toEqual([
      ['agency-diagnostic', 'Free'],
      ['single-report', '$249'],
      ['agency-bundle', '$999'],
    ]);
    expect(FUTURE_PLANS.map((plan) => [plan.name, plan.price])).toEqual([
      ['Starter', '$49/month'],
      ['Professional', '$149/month'],
      ['Enterprise', 'Custom'],
    ]);
  });

  it('renders available concierge offers on the homepage', () => {
    renderWithRouter(<HomePricing />);
    const pricing = document.getElementById('pricing') as HTMLElement;
    for (const offer of CONCIERGE_OFFERS) {
      expect(within(pricing).getByRole('heading', { name: offer.name })).toBeInTheDocument();
      expect(within(pricing).getByText(offer.price)).toBeInTheDocument();
      expect(within(pricing).getByRole('link', { name: offer.cta })).toHaveAttribute(
        'href', '/contact?offer=' + offer.id,
      );
    }
    const copy = pricing.textContent ?? '';
    expect(copy).not.toContain('Jupyter');
    expect(copy).not.toContain('Unlimited projects');
    expect(copy).toContain('No self-service upload');
    expect(copy).toContain('agency owners');
    expect(copy).toContain('Full report and cleaning are not included');
  });

  it('shows concierge pricing, four steps and future-only plans on /pricing', () => {
    renderWithRouter(<PricingPage />, '/pricing');
    const current = document.getElementById('concierge-pricing') as HTMLElement;
    const future = document.getElementById('future-plans') as HTMLElement;
    for (const offer of CONCIERGE_OFFERS) {
      expect(within(current).getByText(offer.price)).toBeInTheDocument();
      expect(within(current).getByRole('link', { name: offer.cta })).toHaveAttribute(
        'href', '/contact?offer=' + offer.id,
      );
    }
    for (const plan of FUTURE_PLANS) {
      expect(within(future).getByText(plan.price)).toBeInTheDocument();
      expect(within(future).getByText(plan.name)).toBeInTheDocument();
    }
    expect(within(future).getAllByText('Coming Soon')).toHaveLength(3);
    expect(within(current).getByText(/limited, human-reviewed data-quality snapshot/)).toBeInTheDocument();
    expect(within(current).getByText(/Full report and cleaning are not included/)).toBeInTheDocument();
    expect(screen.getByText(/free diagnostic is a limited quality snapshot/)).toBeInTheDocument();
    for (const step of ['Upload Data', 'AI Cleaning', 'Choose Analysis', 'Guided Results']) {
      expect(screen.getByRole('heading', { name: step })).toBeInTheDocument();
    }
    expect(screen.getByText(/There is no file upload on this site yet/)).toBeInTheDocument();
    expect(screen.queryByText(/prorate any billing/)).toBeNull();
  });

  it('prefills the contact subject only from whitelisted offer IDs', () => {
    expect(offerRequestSubject('agency-bundle')).toBe('SAINT Concierge Beta — Founding Agency Bundle ($999)');
    expect(offerRequestSubject('agency-diagnostic')).toBe('SAINT Concierge Beta — Agency Diagnostic (Free)');
    expect(offerRequestSubject('first-report')).toBe('');
    expect(offerRequestSubject('<script>')).toBe('');
    expect(offerRequestSubject(null)).toBe('');
    renderWithRouter(<Contact />, '/contact?offer=agency-bundle');
    expect(screen.getByLabelText('Subject')).toHaveValue('SAINT Concierge Beta — Founding Agency Bundle ($999)');
  });
});
