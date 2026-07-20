
import React from 'react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

const Hero = () => {
  const navigate = useNavigate();
  
  const handleStartAnalyzing = () => {
    navigate('/dashboard');
  };

  const handleSignupClick = () => {
    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
      signupForm.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section className="py-20 md:py-28 bg-gradient-to-b from-savvy-white to-savvy-gold/5">
      <div className="container px-4 md:px-6">
        <div className="grid gap-6 lg:grid-cols-2 lg:gap-12 items-center">
          <div className="space-y-4 animate-fade-in">
            <h1 className="text-3xl md:text-5xl font-bold tracking-tighter">
              Clean, Transform, and <span className="text-savvy-gold">Analyze</span> Your Data
            </h1>
            <p className="text-muted-foreground md:text-xl">
              SAINT is a Python-first data cleaning and analytics platform built for data scientists,
              analysts, and business intelligence professionals.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 pt-4">
              <Button 
                size="lg" 
                onClick={handleStartAnalyzing}
                className="bg-savvy-gold hover:bg-savvy-gold/90 text-white"
              >
                Start Analyzing Data
              </Button>
              <Button variant="outline" size="lg" onClick={handleSignupClick}>
                Join Waitlist
              </Button>
            </div>
            <p className="text-sm text-muted-foreground pt-2">
              Upload CSV, JSON, XLSX, XML, or TXT files. AI cleaning included.
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
{`# SAINT Python Integration
import saint as sc

# Load and clean your data
df = sc.clean('messy_data.csv')

# Analyze using descriptive statistics
summary = df.analyze('descriptive')

# Visualize the results
summary.plot(kind='histogram')

# Export the clean data and code
df.to_notebook('analysis.ipynb')`}
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
