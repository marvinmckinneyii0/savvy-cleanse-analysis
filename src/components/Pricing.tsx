import React from 'react';
import { CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { CONCIERGE_OFFERS } from '@/lib/conciergePricing';

/** Service pricing for the human-delivered beta; not a self-serve subscription. */
const Pricing = () => (
  <section className="py-16 bg-white dark:bg-savvy-dark" id="pricing">
    <div className="container px-4 md:px-6">
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold">Data Quality for Marketing Agencies</h2>
        <p className="text-muted-foreground mt-3 max-w-2xl mx-auto">
          Built for agency owners managing client data: start with a limited diagnostic or request a human-reviewed, done-for-you report. No self-service upload, account or subscription is available yet.
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto">
        {CONCIERGE_OFFERS.map((offer) => (
          <div
            key={offer.id}
            className={'flex flex-col rounded-lg border p-6 bg-card text-card-foreground shadow-sm ' +
              (offer.featured ? 'border-savvy-gold shadow-lg' : 'border-border')}
          >
            {offer.featured && (
              <p className="mb-3 text-sm font-semibold text-savvy-gold">Recommended for agencies</p>
            )}
            <h3 className="text-2xl font-bold">{offer.name}</h3>
            <p className="mt-2 text-3xl font-bold">{offer.price}</p>
            <p className="mt-3 text-muted-foreground">{offer.description}</p>
            <ul className="space-y-3 mt-6 mb-7">
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
          </div>
        ))}
      </div>
      <p className="text-center text-sm text-muted-foreground mt-8">
        Agency owner or analyst? In your request, include your agency name, approximate client count and main data challenge. Submit only data you are authorized to share. We confirm eligibility, scope and pricing by email; no checkout is available.
      </p>
      <p className="text-center text-sm mt-3">
        <Link to="/pricing" className="text-savvy-gold underline underline-offset-4 hover:text-savvy-gold/80">
          Compare agency services and future plans
        </Link>
      </p>
    </div>
  </section>
);

export default Pricing;
