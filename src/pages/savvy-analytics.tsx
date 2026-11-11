import React from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';

// Content on this page follows the company site, savvyanalytics.co.
const SITE_URL = 'https://www.savvyanalytics.co';
const SERVICES_URL = `${SITE_URL}/services`;
const BOOKING_URL = `${SITE_URL}/book-online`;
const CONSULTING_EMAIL = 'info@savvyanalytics.co';

const externalLink = { target: '_blank', rel: 'noopener noreferrer' } as const;

const SavvyAnalytics = () => {
  const supportPoints = [
    'Audit and advise on data strategy, automation tools, and business intelligence',
    'Utilize business data to predict patterns and plan for a successful future',
    'Develop digital tools through our preferred partners to enhance business processes',
    'Integrate new digital tools with existing business tools to create seamless workflows',
    'Implement artificial business intelligence to reduce tasks and optimize productivity',
    'Educate business owners and their respective teams to utilize new systems and processes',
  ];

  const stats = [
    { value: '10+', label: 'Years of Experience' },
    { value: '2,000+', label: 'Productivity Hours Saved' },
    { value: '$500K', label: 'Avg. Annual Savings' },
    { value: '9', label: 'Processes Implemented' },
  ];

  const services = [
    {
      title: 'AI Strategy & Roadmaps',
      description:
        'Connect business priorities to practical AI and data opportunities, starting from your workflows, the information you have, and the people who will use the result.',
      features: [
        'Process and data readiness review',
        'Prioritized opportunities',
        'Build-versus-buy recommendation',
        'Phased roadmap with success measures',
      ],
    },
    {
      title: 'Business Solutions & Automation',
      description:
        'Reduce repetitive work and improve handoffs between people, data and software, using the tools you already have where they fit and adding AI only where it helps.',
      features: [
        'Connected workflows and data integration',
        'Human review for important decisions',
        'Operational reporting',
        'Documentation and team adoption',
      ],
    },
    {
      title: 'Custom Software & AI Implementation',
      description:
        'Turn a validated operational need or product idea into a useful application, with users, data, integrations and ownership planned before the build.',
      features: [
        'Client portals and internal tools',
        'Analytics applications',
        'Discovery, prototype, testing and rollout',
        'Access controls, monitoring and handover',
      ],
    },
  ];

  const steps = [
    '30-Minute Discovery Call',
    'Proposal & Recommendations',
    'Project Execution',
    'Project Completion & Launch',
  ];

  return (
    <div className="flex flex-col min-h-screen" data-page="savvy-analytics">
      <Navbar />
      <main className="flex-grow">
        {/* Hero — same layout and classes as the home page hero */}
        <section className="py-20 md:py-28 bg-gradient-to-b from-savvy-white to-savvy-gold/5">
          <div className="container px-4 md:px-6">
            <div className="grid gap-6 lg:grid-cols-2 lg:gap-12 items-center">
              <div className="space-y-4 animate-fade-in">
                <h1 className="text-3xl md:text-5xl font-bold tracking-tighter">
                  Savvy Analytics <span className="text-savvy-gold">Consulting</span>
                </h1>
                <p className="text-muted-foreground md:text-xl">
                  Your partner for AI strategy, automation and business intelligence. Savvy
                  Analytics is the company behind SAINT.
                </p>
                <div className="flex flex-col sm:flex-row gap-3 pt-4">
                  <Button asChild size="lg" className="bg-savvy-gold hover:bg-savvy-gold/90 text-white">
                    <a href={SITE_URL} {...externalLink}>
                      Visit savvyanalytics.co
                    </a>
                  </Button>
                  <Button asChild variant="outline" size="lg">
                    <a href={BOOKING_URL} {...externalLink}>
                      Book a Discovery Call
                    </a>
                  </Button>
                </div>
                <p className="text-sm text-muted-foreground pt-2">
                  Based in Dallas, Texas. Supporting businesses nationwide.
                </p>
              </div>
              <div className="lg:pl-10 animate-fade-in">
                <Card className="shadow-xl">
                  <CardHeader>
                    <CardTitle>How Savvy Analytics Supports Businesses</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="text-sm space-y-3">
                      {supportPoints.map((point) => (
                        <li key={point} className="flex items-start gap-2">
                          <div className="w-1.5 h-1.5 rounded-full bg-savvy-gold mt-2 flex-shrink-0"></div>
                          <span className="text-muted-foreground">{point}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        </section>

        {/* Stats */}
        <section className="py-16 bg-white light-surface" id="results">
          <div className="container px-4 md:px-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {stats.map((stat) => (
                <div key={stat.label} className="text-center">
                  <div className="text-3xl font-bold text-savvy-gold">{stat.value}</div>
                  <div className="text-muted-foreground mt-2">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Services */}
        <section className="py-16 bg-savvy-white light-surface" id="services">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold">Our Services</h2>
              <p className="text-muted-foreground mt-3 max-w-2xl mx-auto">
                Three ways we help organizations put data and AI to work.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {services.map((service) => (
                <Card key={service.title} className="shadow-sm hover:shadow-md transition-shadow">
                  <CardHeader>
                    <CardTitle>{service.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground mb-4">{service.description}</p>
                    <ul className="text-sm space-y-1">
                      {service.features.map((feature) => (
                        <li key={feature} className="flex items-center gap-2">
                          <div className="w-1.5 h-1.5 rounded-full bg-savvy-gold"></div>
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              ))}
            </div>

            <div className="text-center mt-10">
              <Button asChild variant="outline" size="lg">
                <a href={SERVICES_URL} {...externalLink}>
                  See Services on savvyanalytics.co
                </a>
              </Button>
            </div>
          </div>
        </section>

        {/* How projects work — same pattern as the home page "How It Works" */}
        <section className="py-16 bg-savvy-slate/5" id="how-we-work">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold">How We Work</h2>
              <p className="text-muted-foreground mt-3 max-w-2xl mx-auto">
                Every Savvy Analytics project follows four steps.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
              {steps.map((step, index) => (
                <div key={step} className="bg-white dark:bg-card p-4 md:p-6 rounded-lg border shadow-sm">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-savvy-gold text-white mb-4">
                    {index + 1}
                  </div>
                  <h3 className="text-xl font-bold">{step}</h3>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* SAINT */}
        <section className="py-16 bg-white light-surface" id="saint">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold">Where SAINT Fits</h2>
              <p className="text-muted-foreground mt-3 max-w-2xl mx-auto">
                SAINT is built by Savvy Analytics. It turns a CSV into a written data-quality
                report with findings and recommendations. During the beta, our team runs it for
                you.
              </p>
            </div>
            <div className="flex justify-center">
              <Button asChild size="lg" className="bg-savvy-gold hover:bg-savvy-gold/90 text-white">
                <Link to="/contact">Request a Data-Quality Report</Link>
              </Button>
            </div>
          </div>
        </section>

        {/* CTA — same styles as the home page closing section */}
        <section className="py-16 bg-gradient-to-r from-savvy-dark to-savvy-midnight">
          <div className="container px-4 md:px-6 text-center">
            <h2 className="text-3xl font-bold text-white mb-4">Ready to talk about your project?</h2>
            <p className="text-savvy-white/80 max-w-2xl mx-auto mb-8">
              Book a 30-minute discovery call, or email{' '}
              <a href={`mailto:${CONSULTING_EMAIL}`} className="underline hover:text-savvy-gold">
                {CONSULTING_EMAIL}
              </a>
              .
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <Button asChild size="lg" className="bg-savvy-gold hover:bg-savvy-gold/90 text-white">
                <a href={BOOKING_URL} {...externalLink}>
                  Book a Discovery Call
                </a>
              </Button>
              <Button
                asChild
                size="lg"
                variant="outline"
                className="border-white bg-transparent text-white hover:bg-white hover:text-savvy-dark"
              >
                <a href={SITE_URL} {...externalLink}>
                  Visit savvyanalytics.co
                </a>
              </Button>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default SavvyAnalytics;
