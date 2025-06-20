
import React from 'react';
import { Button } from '@/components/ui/button';

const CTA = () => {
  const handleEarlyAccessClick = () => {
    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
      signupForm.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section className="py-16 bg-gradient-to-r from-savvy-dark to-savvy-midnight">
      <div className="container px-4 md:px-6 text-center">
        <h2 className="text-3xl font-bold text-white mb-4">
          Ready to transform your data workflow?
        </h2>
        <p className="text-savvy-white/80 max-w-2xl mx-auto mb-8">
          Join analysts, data scientists, and BI professionals who will use SavvyClean to turn messy data into actionable insights.
        </p>
        <div className="flex flex-col sm:flex-row justify-center gap-4">
          <Button 
            size="lg" 
            onClick={handleEarlyAccessClick}
            className="bg-savvy-gold hover:bg-savvy-gold/90 text-white"
          >
            Get Early Access
          </Button>
        </div>
      </div>
    </section>
  );
};

export default CTA;
