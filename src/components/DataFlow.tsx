
import React from 'react';

const DataFlow = () => {
  const steps = [
    { 
      title: 'Upload Data', 
      description: 'Upload structured or unstructured data in CSV, JSON, XLSX, XML, or TXT formats.' 
    },
    { 
      title: 'AI Cleaning', 
      description: 'Our smart cleaner detects and fixes formatting issues, missing values, and inconsistent schemas.' 
    },
    { 
      title: 'Choose Analysis', 
      description: 'Select from Descriptive, Diagnostic, Predictive, or Prescriptive analytics based on your goals.' 
    },
    { 
      title: 'Guided Results', 
      description: 'Review results with visualizations, formulas, and Python code you can reuse.' 
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
          
          <div className="space-y-10">
            {steps.map((step, index) => (
              <div key={index} className="relative flex items-start gap-6">
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
