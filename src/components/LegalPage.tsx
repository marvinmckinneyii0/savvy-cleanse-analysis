import React from 'react';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import { Alert, AlertDescription } from '@/components/ui/alert';

export interface LegalSection {
  heading: string;
  paragraphs?: string[];
  items?: string[];
}

interface LegalPageProps {
  page: string;
  title: string;
  intro: string;
  /** Shown under the title, for example "Draft of 11 November 2026". */
  version: string;
  sections: LegalSection[];
}

/**
 * Shared layout for the Privacy Policy and Terms pages.
 *
 * Both are drafts until the owner approves them (launch decision D9), so the
 * page carries a visible notice. Remove the notice only when they are approved.
 */
const LegalPage = ({ page, title, intro, version, sections }: LegalPageProps) => (
  <div className="flex flex-col min-h-screen" data-page={page}>
    <Navbar />
    <main className="flex-grow">
      <section className="py-16 bg-white light-surface">
        <div className="container px-4 md:px-6 max-w-3xl mx-auto">
          <h1 className="text-4xl font-bold mb-2">{title}</h1>
          <p className="text-sm text-muted-foreground mb-6">{version}</p>

          <Alert className="mb-8" role="note">
            <p className="font-semibold mb-1">Draft</p>
            <AlertDescription>
              This page is a draft for the SAINT beta and is still under review. It may change
              before it is final.
            </AlertDescription>
          </Alert>

          <p className="text-muted-foreground leading-relaxed mb-10">{intro}</p>

          <div className="space-y-10">
            {sections.map((section) => (
              <section key={section.heading}>
                <h2 className="text-2xl font-semibold mb-3">{section.heading}</h2>
                {section.paragraphs?.map((paragraph) => (
                  <p key={paragraph} className="text-muted-foreground leading-relaxed mb-3">
                    {paragraph}
                  </p>
                ))}
                {section.items && (
                  <ul className="list-disc pl-6 space-y-2 text-muted-foreground leading-relaxed">
                    {section.items.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                )}
              </section>
            ))}
          </div>
        </div>
      </section>
    </main>
    <Footer />
  </div>
);

export default LegalPage;
