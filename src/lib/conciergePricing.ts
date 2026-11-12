/**
 * Public pricing for the human-delivered SAINT concierge beta.
 * Display/lead-request copy only; no checkout or recurring billing.
 * Both pricing surfaces share this source of truth.
 */
export const CONCIERGE_OFFERS = [
  {
    id: 'agency-diagnostic',
    name: 'Agency Diagnostic',
    price: 'Free',
    description: 'A limited, human-reviewed data-quality snapshot for a qualifying marketing agency.',
    features: [
      'One eligible CSV sample; size and scope confirmed before intake',
      'High-level quality risks and recommended next steps',
      'Email delivery of the diagnostic summary',
      'Full report and cleaning are not included',
    ],
    cta: 'Request Agency Diagnostic',
    note: 'For qualifying marketing agencies; limited availability, no automatic approval.',
    featured: false,
  },
  {
    id: 'single-report',
    name: 'Single Client Report',
    price: '$249',
    description: 'For agency owners who need a human-reviewed, done-for-you assessment of one authorized client dataset.',
    features: [
      'One authorized client CSV dataset, up to 100 MB',
      'Data-quality findings, descriptive statistics and comparisons',
      'Word or PDF report with recommendations',
      'Optional rule-based cleaning and cleaned CSV',
    ],
    cta: 'Request Client Report',
    note: 'One-time service; agency must be authorized to share the client data.',
    featured: false,
  },
  {
    id: 'agency-bundle',
    name: 'Founding Agency Bundle',
    price: '$999',
    description: 'Five scoped reports for agency owners responsible for multiple authorized client datasets.',
    features: [
      'Five eligible client CSV reports (one dataset per report)',
      'Data-quality findings, insights and recommendations',
      'Optional rule-based cleaning, documented per report',
      'Human-reviewed scope and email-based delivery',
    ],
    cta: 'Request Founding Agency Bundle',
    note: 'Limited founding-agency offer; scope confirmed first, no auto-renewal.',
    featured: true,
  },
] as const;

export const FUTURE_PLANS = [
  { name: 'Starter', price: '$49/month', description: 'Tentative future small-business / agency entry tier; not sold today.' },
  { name: 'Professional', price: '$149/month', description: 'Tentative future team tier; agency/client capacity and billing still require validation.' },
  { name: 'Enterprise', price: 'Custom', description: 'Future organization-specific and agency capacity arrangements; pricing not set.' },
] as const;

/** Only known offer IDs may populate a contact subject. */
export function offerRequestSubject(offerId: string | null): string {
  const match = CONCIERGE_OFFERS.find((offer) => offer.id === offerId);
  return match ? 'SAINT Concierge Beta — ' + match.name + ' (' + match.price + ')' : '';
}
