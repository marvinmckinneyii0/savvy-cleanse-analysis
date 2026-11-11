
import React from 'react';

const DataFlow = () => {
  const steps = [
    {
      title: 'Upload Data',
      description: 'Request a report with the form below, then share your file by link when we reply. There is no file upload on this site yet. CSV only, up to 100 MB. Please do not send health records, financial account data or government IDs.'
    },
    {
      title: 'AI Cleaning',
      description: 'SAINT checks for missing values, duplicates, outliers and formatting problems. Cleaning is off unless you ask for it: the fixes are rule-based, applied to a copy, and listed in your report. AI writes the report narrative.'
    },
    {
      title: 'Choose Analysis',
      description: 'Tell us what you want to learn from your data. Every report covers summary statistics, trends over time, comparisons between groups and data-quality findings.'
    },
    {
      title: 'Guided Results',
      description: 'You receive a Word or PDF report with findings and recommendations, plus the cleaned CSV if you chose cleaning. We delete your file 7 days after delivery.'
    }
  ];

  return (
    <section className="py-16 bg-savvy-slate/5" id="how-it-works">
      <div className="container px-4 md:px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold">How It Works</h2>
          <p className="text-muted-foreground mt-3 max-w-2xl mx-auto">
            A simple four-step process to transform messy data into actionable insights.
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
