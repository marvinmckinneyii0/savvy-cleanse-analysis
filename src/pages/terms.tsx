import React from 'react';
import LegalPage, { LegalSection } from '@/components/LegalPage';
import { LEAD_FALLBACK_EMAIL } from '@/lib/leadCapture';

const sections: LegalSection[] = [
  {
    heading: 'The service',
    paragraphs: [
      'SAINT is in beta. You send us a CSV file, a person at Savvy Analytics runs SAINT on it, and we email you a written data-quality report. There is no account and no upload on this site.',
      'Because this is a beta, the service may change, and we may not be able to take every request.',
    ],
  },
  {
    heading: 'Your file',
    items: [
      'Send only data you have the right to share with us.',
      'Send CSV files of up to 100 MB, by a shared link.',
      'Do not send health records, financial account data or government ID numbers. We will not process a file that appears to contain them.',
      'Your data stays yours. We use it to produce your report and delete it as described in our Privacy Policy.',
    ],
  },
  {
    heading: 'Cleaning',
    paragraphs: [
      'We clean your data only if you ask us to. Cleaning is applied to a working copy, your original file is not changed, and every change is listed in your report.',
    ],
  },
  {
    heading: 'The report',
    items: [
      'The figures in the report are calculated from the file you sent. If the file is incomplete or wrong, the report will reflect that.',
      'The narrative in the report is written by AI from those figures. It can contain mistakes, so check anything important against the figures.',
      'The report is information to help you understand your data. It is not professional, legal or financial advice, and decisions you make with it are yours.',
      'If a file has a critical data problem, for example a column that is mostly empty, SAINT stops and we cannot produce a report from it. We will tell you what the problem is.',
    ],
  },
  {
    heading: 'Reserving a spot',
    items: [
      'You can reserve a place in line for early access to the self-serve version of SAINT by paying a refundable deposit.',
      'The deposit holds your place. It is not a charge for any report.',
      'We refund the deposit in full if you ask before your access begins.',
      'Deposits are processed by Stripe. The amount is shown on the payment page before you pay.',
    ],
  },
  {
    heading: 'Beta',
    paragraphs: [
      'The beta is provided as it is. We work to make each report accurate, but we do not promise that it has no errors.',
    ],
  },
  {
    heading: 'Contact',
    paragraphs: [`Questions about these terms: ${LEAD_FALLBACK_EMAIL}.`],
  },
];

const Terms = () => (
  <LegalPage
    page="terms"
    title="Terms of Use"
    version="Draft of 11 November 2026"
    intro="These terms cover the SAINT beta. By sending us a request or a file, you agree to them."
    sections={sections}
  />
);

export default Terms;
