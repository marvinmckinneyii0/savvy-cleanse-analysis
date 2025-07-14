
import React from 'react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

const CTA = () => {
  const navigate = useNavigate();
  
  const handleStartNow = () => {
    navigate('/dashboard');
  };

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
          Ready to clean and analyze your data?
        </h2>
        <p className="text-savvy-white/80 max-w-2xl mx-auto mb-8">
          Upload your files now and let our AI cleaner prepare your data for advanced analytics.
        </p>
        <div className="flex flex-col sm:flex-row justify-center gap-4">
          <Button 
            size="lg" 
            onClick={handleStartNow}
            className="bg-savvy-gold hover:bg-savvy-gold/90 text-white"
          >
            Start Analyzing Now
          </Button>
          <Button 
            size="lg" 
            variant="outline"
            onClick={handleEarlyAccessClick}
            className="border-white text-white hover:bg-white hover:text-savvy-dark"
          >
            Join Waitlist
          </Button>
        </div>
      </div>
    </section>
  );
};

export default CTA;
