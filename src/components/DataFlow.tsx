
import React from 'react';

const DataFlow = () => {
  const steps = [
    {
      title: 'Request a Report',
      description: 'Fill in the form with your contact details. There is no file upload on this site.'
    },
    {
      title: 'Send Your CSV',
      description: 'We reply by email with how to share your file by link. CSV only, up to 100 MB. Please do not send health records, financial account data or government IDs.'
    },
    {
      title: 'We Run SAINT',
      description: 'We check data quality, apply cleaning only if you asked for it, and produce your report.'
    },
    {
      title: 'Get Your Report',
      description: 'You receive a Word or PDF report by email, plus the cleaned CSV if you chose cleaning. We delete your file 7 days after delivery.'
    }
  ];

  return (
    <section className="py-16 bg-savvy-slate/5" id="how-it-works">
      <div className="container px-4 md:px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold">How It Works</h2>
          <p className="text-muted-foreground mt-3 max-w-2xl mx-auto">
            Four steps from a messy file to a written report.
          </p>
        </div>
        
        <div className="relative">
          {/* Process line */}
          <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-savvy-gold/20 hidden md:block"></div>
          
          <div className="space-y-8 md:space-y-10">
            {steps.map((step, index) => (
              <div key={index} className="relative flex items-start gap-4 md:gap-6">
                <div className="hidden md:flex items-center justify-center flex-shrink-0 w-8 h-8 rounded-full bg-savvy-gold text-white z-10">
                  {index + 1}
                </div>
                
                <div className="md:pl-4 flex-1 animate-fade-in [animation-delay:200ms]">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="md:hidden flex items-center justify-center w-8 h-8 rounded-full bg-savvy-gold text-white">
                      {index + 1}
                    </div>
                    <h3 className="text-xl font-bold">{step.title}</h3>
                  </div>
                  <p className="text-muted-foreground">{step.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default DataFlow;
