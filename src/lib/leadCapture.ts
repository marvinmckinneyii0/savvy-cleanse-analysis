import { z } from 'zod';

/**
 * Lead capture for the concierge beta (launch decision D5: Formspree).
 *
 * The form ID is public by design (it appears in the POST URL), so it is safe
 * in client code. It is read from VITE_FORMSPREE_FORM_ID at call time.
 * No file upload: customers send data later through the agreed channel.
 */

const FORMSPREE_BASE_URL = 'https://formspree.io/f';

/** Shown when a submission cannot be delivered, so the lead is not lost. */
export const LEAD_FALLBACK_EMAIL = 'support@savvyanalytics.info';

const leadFieldsSchema = z
  .object({
    name: z.string().trim().min(1, 'Please enter your name.').max(200),
    email: z.string().trim().email('Please enter a valid email address.').max(320),
    company: z.string().trim().max(200).optional(),
    subject: z.string().trim().max(200).optional(),
    message: z.string().trim().max(5000).optional(),
  })
  .strict();

export type LeadFields = z.input<typeof leadFieldsSchema>;
export type LeadSource = 'contact' | 'signup';

export type LeadResult =
  | { ok: true }
  | { ok: false; reason: 'invalid' | 'not_configured' | 'failed'; message: string };

const UNAVAILABLE_MESSAGE = `We couldn't send your request. Please email ${LEAD_FALLBACK_EMAIL} instead.`;

function formspreeFormId(): string | null {
  const id = (import.meta.env.VITE_FORMSPREE_FORM_ID as string | undefined)?.trim();
  return id && /^[A-Za-z0-9]+$/.test(id) ? id : null;
}

/**
 * Sends one lead to Formspree.
 *
 * `honeypot` is the value of a field hidden from people. A non-empty value
 * means a bot filled the form: report success and send nothing.
 */
export async function submitLead(
  source: LeadSource,
  fields: LeadFields,
  honeypot = '',
): Promise<LeadResult> {
  if (honeypot.trim() !== '') {
    return { ok: true };
  }

  const parsed = leadFieldsSchema.safeParse(fields);
  if (!parsed.success) {
    return {
      ok: false,
      reason: 'invalid',
      message: parsed.error.issues[0]?.message ?? 'Please check the form and try again.',
    };
  }

  const formId = formspreeFormId();
  if (!formId) {
    return { ok: false, reason: 'not_configured', message: UNAVAILABLE_MESSAGE };
  }

  const payload: Record<string, string> = { source };
  for (const [key, value] of Object.entries(parsed.data)) {
    if (value) payload[key] = value;
  }

  try {
    const response = await fetch(`${FORMSPREE_BASE_URL}/${formId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      return { ok: false, reason: 'failed', message: UNAVAILABLE_MESSAGE };
    }
    return { ok: true };
  } catch {
    return { ok: false, reason: 'failed', message: UNAVAILABLE_MESSAGE };
  }
}
