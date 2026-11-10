
import React from 'react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

const Hero = () => {
  const navigate = useNavigate();
  
  const handleStartAnalyzing = () => {
    navigate('/contact');
  };

  const handleHowItWorksClick = () => {
    const howItWorks = document.getElementById('how-it-works');
    if (howItWorks) {
      howItWorks.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section className="py-20 md:py-28 bg-gradient-to-b from-savvy-white to-savvy-gold/5">
      <div className="container px-4 md:px-6">
        <div className="grid gap-6 lg:grid-cols-2 lg:gap-12 items-center">
          <div className="space-y-4 animate-fade-in">
            <h1 className="text-3xl md:text-5xl font-bold tracking-tighter">
              A <span className="text-savvy-gold">Data-Quality Report</span> on Your CSV, Done for You
            </h1>
            <p className="text-muted-foreground md:text-xl">
              SAINT checks your data for missing values, duplicates, outliers and formatting problems,
              then gives you a written report with findings and recommendations. During the beta,
              our team runs it for you.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 pt-4">
              <Button 
                size="lg" 
                onClick={handleStartAnalyzing}
                className="bg-savvy-gold hover:bg-savvy-gold/90 text-white"
              >
                Request a Data-Quality Report
              </Button>
              <Button variant="outline" size="lg" onClick={handleHowItWorksClick}>
                How It Works
              </Button>
            </div>
            <p className="text-sm text-muted-foreground pt-2">
              CSV files up to 100 MB. There is no upload on this site: we reply by email with how to send your file.
            </p>
          </div>
          <div className="lg:pl-10 animate-fade-in">
            <div className="rounded-lg shadow-xl overflow-hidden border">
              <div className="bg-savvy-dark p-2">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 rounded-full bg-red-500"></div>
                  <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
                  <div className="w-2 h-2 rounded-full bg-green-500"></div>
                </div>
              </div>
              <div className="bg-white dark:bg-savvy-dark/90 p-4">
                <div className="flex items-center mb-4 justify-center">
                  <img 
                    src="/lovable-uploads/1a5ff488-1ca2-4dda-8f25-3e165a31f539.png" 
                    alt="Savvy Analytics Logo" 
                    className="w-12 h-12"
                  />
                </div>
                <pre className="code-block text-xs md:text-sm overflow-x-auto">
{`What's in the report

1. Summary of findings
2. Data quality: missing values, duplicates,
   outliers, types and formats
3. Trends and segment comparisons
4. Unusual values
5. Recommendations
6. Record of cleaning changes
   (only if you asked for cleaning)
7. Findings left for your judgment`}
                </pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
