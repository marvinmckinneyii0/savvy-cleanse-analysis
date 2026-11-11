import React from 'react';
import LegalPage, { LegalSection } from '@/components/LegalPage';
import { LEAD_FALLBACK_EMAIL } from '@/lib/leadCapture';

const sections: LegalSection[] = [
  {
    heading: 'Who we are',
    paragraphs: [
      `SAINT is a service from Savvy Analytics. For anything about your data, email ${LEAD_FALLBACK_EMAIL}.`,
    ],
  },
  {
    heading: 'What we collect',
    items: [
      'Details you enter in a form on this site: your name, email address, company, and the subject and message you write.',
      'The CSV file you choose to send us, by a shared link, after we reply to your request.',
      'The emails you exchange with us.',
    ],
  },
  {
    heading: 'How we use it',
    items: [
      'We use your form details and emails to reply to you and handle your request.',
      'We use your file to produce your data-quality report and, if you asked for cleaning, a cleaned copy of your data.',
      'We do not sell your data.',
    ],
  },
  {
    heading: 'Who else receives it',
    paragraphs: ['We use a small number of outside services to run the beta:'],
    items: [
      'Formspree receives what you enter in our forms and passes it to us by email.',
      'An AI provider writes the narrative in your report. To do that, SAINT sends it figures calculated from your file. These include your column names, summary statistics, and some values taken from the file, such as the most common values in a column and values that look unusual. Your whole file is not sent. The provider is Anthropic; OpenAI or Google are used only if Anthropic is unavailable.',
      'Our email provider carries the messages between us, including the report we send you.',
      'The file-sharing service you choose (for example Google Drive, Dropbox or OneDrive) holds the file you share with us.',
    ],
  },
  {
    heading: 'How long we keep it',
    items: [
      'We delete your file, and any cleaned copy we made, 7 days after we deliver your report.',
      'We keep your contact details and our emails so we can answer follow-up questions. Ask us to delete them at any time.',
    ],
  },
  {
    heading: 'Data we do not accept',
    paragraphs: [
      'Please do not send health records, financial account data or government ID numbers. If a file appears to contain them, we will not process it and will delete it.',
    ],
  },
  {
    heading: 'This website',
    items: [
      'We do not use advertising or analytics cookies.',
      'The site remembers your light or dark theme choice in your browser. That choice stays on your device.',
      'The site loads its fonts from Google Fonts, so Google receives your IP address when the page loads.',
      'The company that hosts the site keeps standard server logs, which include IP addresses.',
    ],
  },
  {
    heading: 'Your choices',
    paragraphs: [
      `You can ask us what we hold about you, ask us to correct it, or ask us to delete it. Email ${LEAD_FALLBACK_EMAIL}.`,
    ],
  },
  {
    heading: 'Changes',
    paragraphs: ['If we change this policy, we will update this page and its date.'],
  },
];

const Privacy = () => (
  <LegalPage
    page="privacy"
    title="Privacy Policy"
    version="Draft of 11 November 2026"
    intro="This policy explains what information we collect during the SAINT beta, what we do with it, and when we delete it."
    sections={sections}
  />
);

export default Privacy;
