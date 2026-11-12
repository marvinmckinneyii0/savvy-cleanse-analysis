import React from 'react';
import { CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Link } from 'react-router-dom';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import DataFlow from '@/components/DataFlow';
import { CONCIERGE_OFFERS, FUTURE_PLANS } from '@/lib/conciergePricing';

const faqs = [
  {
    question: 'Who is the SAINT concierge beta for?',
    answer: 'The founding beta is designed for marketing agency owners and their authorized analysts. Paid reports analyze one eligible client CSV file (up to 100 MB), deliver a Word (.docx) report with findings, and offer optional supported rule-based cleaning on a working copy. The free diagnostic is a limited quality snapshot—not a full report or cleaning service.',
  },
  {
    question: 'How do I submit my data?',
    answer: 'Start with the contact form. We review the request, then reply by email with instructions for sharing your file. There is no self-service upload on this site.',
  },
  {
    question: 'How does the agency bundle work?',
    answer: 'The $999 bundle covers five separate eligible concierge reports. Our team confirms scope and delivery details before accepting a bundle request. It does not renew automatically.',
  },
  {
    question: 'Is a full report included in the free diagnostic?',
    answer: 'No. Eligible marketing agencies may request a limited, human-reviewed data-quality snapshot and next steps at no cost, subject to availability. Full reports are $249 each, or five eligible reports for $999 under the founding-agency bundle. We confirm the scope by email before accepting data.',
  },
  {
    question: 'How are commissioned reports invoiced?',
    answer: 'We confirm scope, price, invoice details and payment instructions in writing before accepting work. Requesting a report is not an online purchase; there is no report checkout or automatic renewal.',
  },
  {
    question: 'Do you offer ongoing agency subscriptions?',
    answer: 'Not yet. The published Starter ($49/month), Professional ($149/month) and Enterprise (custom) tiers are tentative future self-service concepts, not purchasable offers. Agency/client capacity and per-client billing will be evaluated with agency owners before launch.',
  },
];

const PricingPage = () => (
  <div className="flex flex-col min-h-screen" data-page="pricing">
    <Navbar />
    <main className="flex-grow">
      <section className="py-20 md:py-28 bg-gradient-to-b from-savvy-white to-savvy-gold/5">
        <div className="container px-4 md:px-6 text-center max-w-4xl mx-auto">
          <h1 className="text-3xl md:text-5xl font-bold tracking-tighter mb-6">
            Simple, Transparent <span className="text-savvy-gold">Pricing</span>
          </h1>
          <p className="text-muted-foreground md:text-xl max-w-2xl mx-auto">
            For marketing agency owners managing client data: begin with a limited diagnostic or commission a reviewed, done-for-you report. Each agency request is scoped before acceptance.
          </p>
        </div>
      </section>

      <section className="py-16 bg-white light-surface" id="concierge-pricing">
        <div className="container px-4 md:px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold">Founding Agency Concierge Beta</h2>
            <p className="text-muted-foreground mt-3 max-w-2xl mx-auto">
              Designed for agency owners and authorized analysts. Paid reports support eligible CSV datasets up to 100 MB; the free diagnostic has a separately confirmed limited scope. No self-service account, upload or recurring subscription yet.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto">
            {CONCIERGE_OFFERS.map((offer) => (
              <Card key={offer.id} className={'flex flex-col shadow-sm ' + (offer.featured ? 'border-savvy-gold shadow-lg' : '')}>
                <CardHeader>
                  {offer.featured && (
                    <p className="text-sm font-semibold text-savvy-gold">Recommended for agencies</p>
                  )}
                  <CardTitle className="text-2xl font-bold">{offer.name}</CardTitle>
                  <p className="text-3xl font-bold mt-3">{offer.price}</p>
                  <p className="text-muted-foreground text-sm mt-2">{offer.description}</p>
                </CardHeader>
                <CardContent className="flex flex-col flex-1">
                  <ul className="space-y-3 mb-6">
                    {offer.features.map((feature) => (
                      <li key={feature} className="flex items-start gap-2 text-sm">
                        <CheckCircle2 className="h-5 w-5 text-savvy-gold flex-shrink-0" aria-hidden="true" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <div className="mt-auto">
                    <Button asChild className="w-full bg-savvy-gold text-savvy-dark hover:bg-savvy-gold/90">
                      <Link to={'/contact?offer=' + offer.id}>{offer.cta}</Link>
                    </Button>
                    <p className="mt-3 text-xs text-muted-foreground">{offer.note}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          <p className="mt-8 text-center text-sm text-muted-foreground">
            Please include your agency name, approximate number of client accounts, and the quality or reporting problem you need solved. Only submit data your agency is authorized to process. Scope, availability and price are confirmed before any paid work; no checkout is available here.
          </p>
        </div>
      </section>

      <DataFlow />

      <section className="py-16 bg-white light-surface" id="future-plans">
        <div className="container px-4 md:px-6">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold">Future Agency & Team Software — Coming Soon</h2>
            <p className="text-muted-foreground mt-3 max-w-2xl mx-auto">
              Future self-service concepts only: tentative prices, not available to buy. We intend to validate agency pricing against client count, reporting volume and delivery costs before any release.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {FUTURE_PLANS.map((plan) => (
              <Card key={plan.name} className="shadow-sm">
                <CardHeader>
                  <CardTitle>{plan.name}</CardTitle>
                  <p className="text-2xl font-bold mt-2">{plan.price}</p>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">{plan.description}</p>
                  <p className="text-sm font-semibold mt-4 text-savvy-gold">Coming Soon</p>
                </CardContent>
              </Card>
            ))}
          </div>
          <div className="text-center mt-8">
            <Button asChild variant="outline"><Link to="/contact">Ask About Early Access</Link></Button>
          </div>
        </div>
      </section>

      <section className="py-16 bg-savvy-slate/5" id="pricing-faq">
        <div className="container px-4 md:px-6">
          <h2 className="text-3xl font-bold text-center mb-10">Frequently Asked Questions</h2>
          <div className="max-w-3xl mx-auto space-y-5">
            {faqs.map((faq) => (
              <Card key={faq.question} className="shadow-sm">
                <CardContent className="p-6">
                  <h3 className="font-semibold mb-2">{faq.question}</h3>
                  <p className="text-muted-foreground">{faq.answer}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>
    </main>
    <Footer />
  </div>
);

export default PricingPage;
