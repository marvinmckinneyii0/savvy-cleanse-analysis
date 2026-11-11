import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import DataFlow from '@/components/DataFlow';
import EarlyAccess from '@/components/EarlyAccess';
import Roadmap from '@/components/Roadmap';
import { DATA_SOURCES } from '@/lib/dataSources';
import { reservationLink } from '@/lib/reservation';
import Privacy from '@/pages/privacy';
import Terms from '@/pages/terms';

const fetchMock = vi.fn();

const renderIn = (element: JSX.Element) => render(<MemoryRouter>{element}</MemoryRouter>);

beforeEach(() => {
  fetchMock.mockReset();
  fetchMock.mockResolvedValue({ ok: true });
  vi.stubGlobal('fetch', fetchMock);
  vi.stubEnv('VITE_FORMSPREE_FORM_ID', 'testform123');
  vi.stubEnv('VITE_STRIPE_PAYMENT_LINK', '');
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
  vi.unstubAllEnvs();
});

describe('How It Works', () => {
  it('uses the original four step titles, in order', () => {
    renderIn(<DataFlow />);

    const titles = screen.getAllByRole('heading', { level: 3 }).map((h) => h.textContent);
    expect(titles).toEqual(['Upload Data', 'AI Cleaning', 'Choose Analysis', 'Guided Results']);
  });

  it('describes what actually happens today', () => {
    const text = renderIn(<DataFlow />).container.textContent ?? '';

    expect(text).toMatch(/There is no file upload on this site yet/);
    expect(text).toMatch(/CSV only, up to 100 MB/);
    expect(text).toMatch(/Cleaning is off unless you ask for it/);
    expect(text).toMatch(/rule-based/);
    expect(text).not.toMatch(/JSON|XLSX|XML|predictive|prescriptive|Python/i);
  });
});

describe('Data Sources Roadmap', () => {
  it('lists the sources in the planned order with CSV as the only one available', () => {
    renderIn(<Roadmap />);
    const items = within(screen.getByRole('list')).getAllByRole('listitem');

    expect(items.map((item) => item.querySelector('h3')?.textContent)).toEqual([
      'CSV files',
      'Excel workbooks',
      'JSON files',
      'Connections to your tools',
      'Documents and AI search (RAG)',
    ]);
    expect(DATA_SOURCES.filter((source) => source.status === 'Available now').map((s) => s.id)).toEqual(['csv']);
  });

  it('gives no dates', () => {
    const text = renderIn(<Roadmap />).container.textContent ?? '';

    expect(text).toMatch(/not a schedule/);
    expect(text).not.toMatch(/\b20\d\d\b|\bQ[1-4]\b|January|February|March|April|June|July|August|September|October|November|December/);
  });

  it('is a white band that keeps its text readable in dark mode', () => {
    const section = renderIn(<Roadmap />).container.querySelector('section') as HTMLElement;

    expect(section.className).toContain('bg-white light-surface');
  });
});

describe('interest list', () => {
  it('sends the picked interests to Formspree as an interest lead', async () => {
    const user = userEvent.setup();
    renderIn(<EarlyAccess />);

    await user.type(screen.getByLabelText('Full Name'), 'Ada Lovelace');
    await user.type(screen.getByLabelText('Work Email'), 'ada@example.com');
    await user.click(screen.getByRole('checkbox', { name: 'Excel workbooks' }));
    await user.click(screen.getByRole('checkbox', { name: 'Connections to your tools' }));
    await user.click(screen.getByRole('button', { name: 'Join the List' }));

    await waitFor(() => expect(screen.getByText("You're on the list")).toBeInTheDocument());
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      source: 'interest',
      name: 'Ada Lovelace',
      email: 'ada@example.com',
      interests: 'Excel workbooks, Connections to your tools',
    });
  });

  it('offers only items that are not available yet, plus the web app', () => {
    renderIn(<EarlyAccess />);
    const labels = screen.getAllByRole('checkbox').map((box) => box.getAttribute('id'));

    expect(labels).toEqual([
      'interest-excel',
      'interest-json',
      'interest-api',
      'interest-documents',
      'interest-web-app',
    ]);
  });

  it('shows an error and keeps the entries when delivery fails', async () => {
    fetchMock.mockResolvedValue({ ok: false, status: 500 });
    const user = userEvent.setup();
    renderIn(<EarlyAccess />);

    await user.type(screen.getByLabelText('Full Name'), 'Ada Lovelace');
    await user.type(screen.getByLabelText('Work Email'), 'ada@example.com');
    await user.click(screen.getByRole('button', { name: 'Join the List' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('info@savvyanalytics.co');
    expect(screen.getByLabelText('Work Email')).toHaveValue('ada@example.com');
  });
});

describe('reserve a spot', () => {
  it('is hidden when no payment link is set', () => {
    renderIn(<EarlyAccess />);

    expect(screen.queryByText('Reserve Your Spot', { selector: 'a' })).not.toBeInTheDocument();
    expect(reservationLink()).toBeNull();
  });

  it('ignores a link that is not a Stripe Payment Link', () => {
    for (const bad of [
      'http://buy.stripe.com/abc123',
      'https://evil.example.com/abc123',
      'https://buy.stripe.com.evil.example/abc',
      'javascript:alert(1)',
    ]) {
      vi.stubEnv('VITE_STRIPE_PAYMENT_LINK', bad);
      expect(reservationLink()).toBeNull();
    }
  });

  it('links to the Stripe Payment Link in a new tab and states the deposit is refundable', () => {
    vi.stubEnv('VITE_STRIPE_PAYMENT_LINK', 'https://buy.stripe.com/test_abc123');
    const { container } = renderIn(<EarlyAccess />);
    const link = screen.getByRole('link', { name: 'Reserve Your Spot' });

    expect(link).toHaveAttribute('href', 'https://buy.stripe.com/test_abc123');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link.getAttribute('rel')).toContain('noopener');
    expect(container.textContent).toMatch(/refundable deposit/);
    expect(container.textContent).toMatch(/refund the deposit in full if you ask before your access begins/);
    // The amount lives on the Stripe page, never in the site.
    expect(container.textContent).not.toMatch(/\$|USD|€|£/);
  });
});

describe('legal pages cover the new forms and the deposit', () => {
  it('the privacy policy discloses Stripe and the interest selections', () => {
    const text = renderIn(<Privacy />).container.textContent ?? '';

    expect(text).toMatch(/Stripe processes your deposit/);
    expect(text).toMatch(/never your full card number/);
    expect(text).toMatch(/which upcoming features you are interested in/);
  });

  it('the terms explain the refundable reservation', () => {
    const text = renderIn(<Terms />).container.textContent ?? '';

    expect(text).toMatch(/Reserving a spot/);
    expect(text).toMatch(/refund the deposit in full if you ask before your access begins/);
    expect(text).toMatch(/It is not a charge for any report/);
  });
});
