
import React from 'react';
import { CheckIcon, XIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';

const Pricing = () => {
  const plans = [
    {
      name: 'Free',
      price: '$0',
      description: 'Perfect for getting started with basic data cleaning and descriptive analytics.',
      features: [
        'Data upload and basic cleaning',
        'Descriptive analytics',
        'Basic visualizations',
        'CSV export',
        '5 projects',
        '10MB file size limit',
      ],
      notIncluded: [
        'Advanced transformations',
        'Diagnostic analytics',
        'Predictive analytics',
        'Prescriptive analytics',
        'Jupyter/IPython export',
        'API access',
      ],
      buttonText: 'Start for Free',
      buttonVariant: 'outline'
    },
    {
      name: 'Pro',
      price: '$29',
      period: '/month',
      description: 'Full access to all analytics types and advanced features for professionals.',
      features: [
        'Advanced data cleaning',
        'All analytics types',
        'Advanced visualizations',
        'Jupyter notebook export',
        'Python code generation',
        'Unlimited projects',
        '50MB file size limit',
        'API access',
      ],
      notIncluded: [],
      buttonText: 'Upgrade to Pro',
      buttonVariant: 'default',
      highlight: true
    }
  ];

  return (
    <section className="py-16 bg-white" id="pricing">
      <div className="container px-4 md:px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold">Pricing Plans</h2>
          <p className="text-muted-foreground mt-3 max-w-2xl mx-auto">
            Choose the plan that fits your needs, from free data cleaning to advanced analytics.
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {plans.map((plan) => (
            <div 
              key={plan.name}
              className={`rounded-lg border ${
                plan.highlight 
                  ? 'border-savvy-blue shadow-lg shadow-savvy-blue/10' 
                  : 'border-border shadow-sm'
              } p-6`}
            >
              <div className="mb-6">
                <h3 className="text-2xl font-bold">{plan.name}</h3>
                <div className="mt-2 flex items-end">
                  <span className="text-3xl font-bold">{plan.price}</span>
                  {plan.period && <span className="text-muted-foreground ml-1">{plan.period}</span>}
                </div>
                <p className="mt-3 text-muted-foreground">{plan.description}</p>
              </div>
              
              <div className="space-y-3 mb-6">
                {plan.features.map((feature) => (
                  <div key={feature} className="flex items-start">
                    <CheckIcon className="h-5 w-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span>{feature}</span>
                  </div>
                ))}
                
                {plan.notIncluded.map((feature) => (
                  <div key={feature} className="flex items-start text-muted-foreground">
                    <XIcon className="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
                    <span>{feature}</span>
                  </div>
                ))}
              </div>
              
              <Link to="/dashboard">
                <Button 
                  variant={plan.buttonVariant as "outline" | "default"} 
                  className={`w-full ${plan.highlight ? 'bg-savvy-blue hover:bg-savvy-blue/90' : ''}`}
                >
                  {plan.buttonText}
                </Button>
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Pricing;
