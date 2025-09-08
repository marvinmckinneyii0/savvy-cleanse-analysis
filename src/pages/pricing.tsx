import React from 'react';
import { CheckIcon, XIcon, Star } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import { Link } from 'react-router-dom';

const Pricing = () => {
  const plans = [
    {
      name: 'Starter',
      price: '$29',
      period: '/month',
      description: 'For individuals and students getting started with data analytics.',
      features: [
        '5 datasets per month',
        'Basic cleaning tools',
        'Descriptive analytics',
        'Standard visualizations',
        'CSV/Excel export',
        'Email support',
      ],
      notIncluded: [
        'Diagnostic analytics',
        'Predictive analytics',
        'Prescriptive analytics',
        'Jupyter notebook export',
        'API access',
        'Priority support',
      ],
      buttonText: 'Start with Starter',
      buttonVariant: 'outline',
      popular: false,
    },
    {
      name: 'Growth',
      price: '$79',
      period: '/month',
      description: 'For small teams who need comprehensive analytics capabilities.',
      features: [
        'Unlimited datasets',
        'All analytics modes',
        'Advanced cleaning tools',
        'Interactive dashboards',
        'Export to CSV/Excel',
        'Basic team dashboard',
        'Jupyter notebook export',
        'Priority email support',
      ],
      notIncluded: [
        'Custom integrations',
        'Dedicated support',
        'SLA guarantees',
        'Admin dashboard',
      ],
      buttonText: 'Choose Growth',
      buttonVariant: 'default',
      popular: true,
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: 'pricing',
      description: 'For larger organizations with advanced requirements.',
      features: [
        'Everything in Growth',
        'Dedicated support team',
        'Advanced ML features',
        'Custom integrations',
        'SLA + admin dashboard',
        'On-premise deployment',
        'Custom training',
        'White-label options',
      ],
      notIncluded: [],
      buttonText: 'Contact Sales',
      buttonVariant: 'outline',
      popular: false,
    },
  ];

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <main className="flex-grow">
        {/* Hero Section */}
        <section className="py-16 bg-gradient-to-br from-savvy-dark via-savvy-midnight to-savvy-slate text-white">
          <div className="container px-4 md:px-6">
            <div className="text-center max-w-4xl mx-auto">
              <h1 className="text-4xl md:text-5xl font-bold mb-6">
                Simple, Transparent
                <span className="text-savvy-gold"> Pricing</span>
              </h1>
              <p className="text-xl text-gray-300 max-w-2xl mx-auto">
                Choose the plan that fits your data analytics needs. Start free, upgrade when you're ready.
              </p>
            </div>
          </div>
        </section>

        {/* Pricing Cards */}
        <section className="py-16 bg-white dark:bg-savvy-dark">
          <div className="container px-4 md:px-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8 max-w-6xl mx-auto">
              {plans.map((plan) => (
                <Card
                  key={plan.name}
                  className={`relative ${
                    plan.popular
                      ? 'border-savvy-blue shadow-lg shadow-savvy-blue/20 scale-105'
                      : 'border-border shadow-sm'
                  } transition-all duration-300 hover:shadow-lg`}
                >
                  {plan.popular && (
                    <Badge className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-savvy-blue text-white">
                      <Star className="h-3 w-3 mr-1" />
                      Most Popular
                    </Badge>
                  )}
                  
                  <CardHeader className="text-center pb-2">
                    <CardTitle className="text-2xl font-bold">{plan.name}</CardTitle>
                    <div className="mt-4 flex items-end justify-center">
                      <span className="text-4xl font-bold">{plan.price}</span>
                      {plan.period && (
                        <span className="text-muted-foreground ml-1 mb-1">{plan.period}</span>
                      )}
                    </div>
                    <p className="mt-3 text-muted-foreground text-sm">{plan.description}</p>
                  </CardHeader>
                  
                  <CardContent className="pt-4">
                    <div className="space-y-3 mb-6">
                      {plan.features.map((feature) => (
                        <div key={feature} className="flex items-start">
                          <CheckIcon className="h-5 w-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                          <span className="text-sm">{feature}</span>
                        </div>
                      ))}
                      
                      {plan.notIncluded.map((feature) => (
                        <div key={feature} className="flex items-start text-muted-foreground">
                          <XIcon className="h-5 w-5 mr-3 mt-0.5 flex-shrink-0" />
                          <span className="text-sm">{feature}</span>
                        </div>
                      ))}
                    </div>
                    
                    <Link to="/dashboard" className="block">
                      <Button
                        variant={plan.buttonVariant as "outline" | "default"}
                        className={`w-full ${
                          plan.popular ? 'bg-savvy-blue hover:bg-savvy-blue/90' : ''
                        }`}
                      >
                        {plan.buttonText}
                      </Button>
                    </Link>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* FAQ Section */}
        <section className="py-16 bg-gradient-to-r from-savvy-blue/5 to-savvy-gold/5">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">Frequently Asked Questions</h2>
            </div>
            
            <div className="max-w-3xl mx-auto space-y-6">
              <div className="bg-white dark:bg-card rounded-lg p-6 shadow-sm">
                <h3 className="font-semibold mb-2">Can I change plans at any time?</h3>
                <p className="text-muted-foreground">
                  Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately, and we'll prorate any billing adjustments.
                </p>
              </div>
              
              <div className="bg-white dark:bg-card rounded-lg p-6 shadow-sm">
                <h3 className="font-semibold mb-2">What happens to my data if I cancel?</h3>
                <p className="text-muted-foreground">
                  Your data remains accessible for 30 days after cancellation. You can export all your projects and cleaned datasets during this period.
                </p>
              </div>
              
              <div className="bg-white dark:bg-card rounded-lg p-6 shadow-sm">
                <h3 className="font-semibold mb-2">Do you offer discounts for students or nonprofits?</h3>
                <p className="text-muted-foreground">
                  Yes! We offer 50% discounts for verified students and qualifying nonprofit organizations. Contact us for more details.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default Pricing;