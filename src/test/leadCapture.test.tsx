import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import SignupForm from '@/components/SignupForm';
import Contact from '@/pages/contact';
import { LEAD_FALLBACK_EMAIL, submitLead } from '@/lib/leadCapture';

const VALID = { name: 'Ada Lovelace', email: 'ada@example.com', company: 'Analytical Engines' };

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  fetchMock.mockResolvedValue({ ok: true });
  vi.stubGlobal('fetch', fetchMock);
  vi.stubEnv('VITE_FORMSPREE_FORM_ID', 'testform123');
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe('submitLead', () => {
  it('posts the lead as JSON to the configured Formspree form', async () => {
    const result = await submitLead('signup', VALID);

    expect(result).toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('https://formspree.io/f/testform123');
    expect(init.method).toBe('POST');
    expect(init.headers.Accept).toBe('application/json');
    expect(JSON.parse(init.body)).toEqual({ source: 'signup', ...VALID });
  });

  it('trims values and omits empty optional fields', async () => {
    await submitLead('contact', { name: '  Ada ', email: ' ada@example.com ', subject: '  ' });

    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      source: 'contact',
      name: 'Ada',
      email: 'ada@example.com',
    });
  });

  it('rejects an invalid email without sending', async () => {
    const result = await submitLead('contact', { ...VALID, email: 'not-an-email' });

    expect(result).toMatchObject({ ok: false, reason: 'invalid' });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('reports success but sends nothing when the honeypot is filled', async () => {
    const result = await submitLead('signup', VALID, 'i-am-a-bot');

    expect(result).toEqual({ ok: true });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('fails with the fallback email when the form ID is not configured', async () => {
    vi.stubEnv('VITE_FORMSPREE_FORM_ID', '');

    const result = await submitLead('signup', VALID);

    expect(result).toMatchObject({ ok: false, reason: 'not_configured' });
    expect(result.ok === false && result.message).toContain(LEAD_FALLBACK_EMAIL);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('refuses a form ID that is not alphanumeric', async () => {
    vi.stubEnv('VITE_FORMSPREE_FORM_ID', '../other/path');

    const result = await submitLead('signup', VALID);

    expect(result).toMatchObject({ ok: false, reason: 'not_configured' });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('fails when Formspree responds with an error status', async () => {
    fetchMock.mockResolvedValue({ ok: false, status: 500 });

    expect(await submitLead('signup', VALID)).toMatchObject({ ok: false, reason: 'failed' });
  });

  it('fails when the network request throws', async () => {
    fetchMock.mockRejectedValue(new TypeError('network down'));

    expect(await submitLead('signup', VALID)).toMatchObject({ ok: false, reason: 'failed' });
  });
});

describe('SignupForm', () => {
  const fillAndSubmit = async () => {
    const user = userEvent.setup();
    render(<SignupForm />);
    await user.type(screen.getByLabelText('Full Name'), VALID.name);
    await user.type(screen.getByLabelText('Work Email'), VALID.email);
    await user.type(screen.getByLabelText('Company'), VALID.company);
    await user.click(screen.getByRole('button', { name: 'Join Waitlist' }));
  };

  it('sends the lead and shows the thank-you state', async () => {
    await fillAndSubmit();

    await waitFor(() => expect(screen.getByText('Thank you!')).toBeInTheDocument());
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ source: 'signup', ...VALID });
  });

  it('shows an error and keeps the typed values when delivery fails', async () => {
    fetchMock.mockResolvedValue({ ok: false, status: 500 });

    await fillAndSubmit();

    expect(await screen.findByRole('alert')).toHaveTextContent(LEAD_FALLBACK_EMAIL);
    expect(screen.queryByText('Thank you!')).not.toBeInTheDocument();
    expect(screen.getByLabelText('Work Email')).toHaveValue(VALID.email);
  });
});

describe('Contact page form', () => {
  const fillAndSubmit = async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <Contact />
      </MemoryRouter>,
    );
    await user.type(screen.getByLabelText('Name'), VALID.name);
    await user.type(screen.getByLabelText('Email'), VALID.email);
    await user.type(screen.getByLabelText('Subject'), 'Data-quality report');
    await user.type(screen.getByLabelText('Message'), 'Please review our sales export.');
    await user.click(screen.getByRole('button', { name: 'Send Message' }));
  };

  it('sends the message and confirms it was sent', async () => {
    await fillAndSubmit();

    expect(await screen.findByRole('status')).toHaveTextContent('your message was sent');
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      source: 'contact',
      name: VALID.name,
      email: VALID.email,
      subject: 'Data-quality report',
      message: 'Please review our sales export.',
    });
    expect(screen.getByLabelText('Message')).toHaveValue('');
  });

  it('shows an error and keeps the message when delivery fails', async () => {
    fetchMock.mockRejectedValue(new TypeError('network down'));

    await fillAndSubmit();

    expect(await screen.findByRole('alert')).toHaveTextContent(LEAD_FALLBACK_EMAIL);
    expect(screen.getByLabelText('Message')).toHaveValue('Please review our sales export.');
  });
});
