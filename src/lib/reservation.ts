/**
 * Reserve-a-spot deposit (owner decision, 2026-11-11): a refundable deposit
 * taken through a Stripe Payment Link that the owner creates and prices in the
 * Stripe dashboard. The site only links to it, so no card data and no amount
 * live in this code.
 *
 * The link is read from VITE_STRIPE_PAYMENT_LINK. Anything that is not a
 * Stripe-hosted payment link is ignored, and the reserve option stays hidden.
 */
const STRIPE_PAYMENT_LINK = /^https:\/\/buy\.stripe\.com\/[A-Za-z0-9_-]+$/;

export function reservationLink(): string | null {
  const link = (import.meta.env.VITE_STRIPE_PAYMENT_LINK as string | undefined)?.trim();
  return link && STRIPE_PAYMENT_LINK.test(link) ? link : null;
}
