import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import { Building2, Target, Users, Globe, ExternalLink, ArrowRight, CheckCircle } from 'lucide-react';

const SavvyAnalytics = () => {
  const services = [
    {
      title: "AI Strategy Consulting",
      description: "Develop comprehensive AI strategies aligned with your business objectives and organizational capabilities.",
      features: [
        "AI readiness assessment",
        "Strategic roadmap development",
        "Technology stack recommendations",
        "ROI modeling and projections"
      ]
    },
    {
      title: "Process Automation",
      description: "Streamline operations with intelligent automation solutions that scale with your business.",
      features: [
        "Workflow analysis and optimization",
        "Custom automation solutions",
        "Integration with existing systems",
        "Change management support"
      ]
    },
    {
      title: "Analytics Solutions",
      description: "Transform data into actionable insights with custom analytics platforms and reporting systems.",
      features: [
        "Data warehouse design",
        "Custom dashboard development",
        "Predictive analytics models",
        "Real-time monitoring systems"
      ]
    }
  ];

  const industries = [
    { name: "Financial Services", description: "Risk analysis, fraud detection, and regulatory compliance" },
    { name: "Healthcare", description: "Patient analytics, operational efficiency, and clinical insights" },
    { name: "Manufacturing", description: "Predictive maintenance, quality control, and supply chain optimization" },
    { name: "Retail & E-commerce", description: "Customer analytics, inventory optimization, and personalization" },
    { name: "Technology", description: "Product analytics, user behavior analysis, and performance optimization" },
    { name: "Energy & Utilities", description: "Demand forecasting, grid optimization, and sustainability analytics" }
  ];

  const regions = [
    { region: "United States", markets: "New York, San Francisco, Austin, Chicago" },
    { region: "Europe", markets: "Lisbon, London, Berlin, Amsterdam" }
  ];

  const stats = [
    { value: "50+", label: "Projects Delivered" },
    { value: "20+", label: "Enterprise Clients" },
    { value: "95%", label: "Client Retention" },
    { value: "3 Years", label: "Average Engagement" }
  ];

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <main className="flex-grow">
        {/* Hero Section */}
        <section className="py-16 bg-gradient-to-br from-savvy-dark via-savvy-midnight to-savvy-slate text-white">
          <div className="container px-4 md:px-6">
            <div className="text-center max-w-4xl mx-auto">
              <Building2 className="h-16 w-16 text-savvy-gold mx-auto mb-6" />
              <h1 className="text-4xl md:text-5xl font-bold mb-6">
                <span className="text-savvy-gold">Savvy Analytics</span>
                <br />Consulting
              </h1>
              <p className="text-xl text-gray-300 max-w-2xl mx-auto mb-8">
                We help businesses in the U.S. and Europe adopt AI responsibly through strategic consulting, automation, and custom analytics solutions.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button className="bg-savvy-gold text-savvy-dark hover:bg-savvy-gold/90">
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Visit savvyanalytics.info
                </Button>
                <Button variant="outline" className="border-white text-white hover:bg-white/10">
                  Learn About Our Services
                </Button>
              </div>
            </div>
          </div>
        </section>

        {/* Stats */}
        <section className="py-12 bg-white dark:bg-savvy-dark border-b">
          <div className="container px-4 md:px-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-4xl mx-auto">
              {stats.map((stat, index) => (
                <div key={index} className="text-center">
                  <div className="text-3xl md:text-4xl font-bold text-savvy-blue mb-2">
                    {stat.value}
                  </div>
                  <div className="text-muted-foreground">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* About */}
        <section className="py-16 bg-gradient-to-r from-savvy-blue/5 to-savvy-gold/5">
          <div className="container px-4 md:px-6">
            <div className="max-w-4xl mx-auto text-center">
              <h2 className="text-3xl font-bold mb-8">About Savvy Analytics</h2>
              <div className="bg-white dark:bg-card rounded-lg p-8 shadow-sm">
                <p className="text-lg text-muted-foreground leading-relaxed mb-6">
                  Savvy Analytics is the parent company behind SAINT, specializing in AI strategy, 
                  automation, and analytics solutions for businesses across the United States and Europe. 
                  We believe in responsible AI adoption that drives real business value while maintaining 
                  transparency and ethical standards.
                </p>
                <div className="flex items-center justify-center gap-8 text-sm text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <Globe className="h-4 w-4" />
                    Global Reach
                  </div>
                  <div className="flex items-center gap-2">
                    <Target className="h-4 w-4" />
                    Strategic Focus
                  </div>
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4" />
                    Expert Team
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Services */}
        <section className="py-16 bg-white dark:bg-savvy-dark">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">Our Services</h2>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                Comprehensive AI and analytics consulting services designed to transform your business operations.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
              {services.map((service, index) => (
                <Card key={index} className="shadow-sm hover:shadow-lg transition-all duration-300 h-full">
                  <CardHeader>
                    <CardTitle className="text-xl">{service.title}</CardTitle>
                  </CardHeader>
                  <CardContent className="flex flex-col h-full">
                    <p className="text-muted-foreground mb-6 flex-grow">
                      {service.description}
                    </p>
                    <div className="space-y-2">
                      {service.features.map((feature, featureIndex) => (
                        <div key={featureIndex} className="flex items-start gap-2">
                          <CheckCircle className="h-4 w-4 text-savvy-blue mt-0.5 flex-shrink-0" />
                          <span className="text-sm">{feature}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Industries */}
        <section className="py-16 bg-gradient-to-r from-savvy-blue/5 to-savvy-gold/5">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">Industries We Serve</h2>
              <p className="text-muted-foreground">
                Deep expertise across multiple industries with tailored solutions for each sector.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
              {industries.map((industry, index) => (
                <Card key={index} className="shadow-sm hover:shadow-lg transition-all duration-300">
                  <CardContent className="p-6">
                    <h3 className="font-semibold mb-2">{industry.name}</h3>
                    <p className="text-muted-foreground text-sm">{industry.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Geographic Presence */}
        <section className="py-16 bg-white dark:bg-savvy-dark">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">Global Presence</h2>
              <p className="text-muted-foreground">
                Serving clients across key markets in the United States and Europe.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
              {regions.map((region, index) => (
                <Card key={index} className="shadow-sm">
                  <CardHeader>
                    <CardTitle className="text-xl flex items-center gap-2">
                      <Globe className="h-5 w-5 text-savvy-blue" />
                      {region.region}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground">{region.markets}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* SAINT Connection */}
        <section className="py-16 bg-gradient-to-r from-savvy-blue/5 to-savvy-gold/5">
          <div className="container px-4 md:px-6">
            <div className="max-w-4xl mx-auto text-center">
              <h2 className="text-3xl font-bold mb-6">The SAINT Connection</h2>
              <Card className="shadow-lg">
                <CardContent className="p-8">
                  <p className="text-lg text-muted-foreground leading-relaxed mb-6">
                    SAINT was born from our consulting experience. After helping dozens of organizations 
                    with data analytics challenges, we identified a common pain point: the time-consuming, 
                    error-prone process of data cleaning and preparation. SAINT is our solution to 
                    democratize access to clean, reliable data analytics.
                  </p>
                  <div className="flex flex-col sm:flex-row gap-4 justify-center">
                    <Button className="bg-savvy-blue hover:bg-savvy-blue/90">
                      Try SAINT
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </Button>
                    <Button variant="outline">
                      Learn About Our Consulting
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-16 bg-gradient-to-br from-savvy-dark via-savvy-midnight to-savvy-slate text-white">
          <div className="container px-4 md:px-6">
            <div className="text-center max-w-3xl mx-auto">
              <h2 className="text-3xl font-bold mb-4">Ready to Transform Your Business?</h2>
              <p className="text-gray-300 mb-8">
                Let's discuss how Savvy Analytics can help you adopt AI responsibly and drive meaningful business outcomes.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button className="bg-savvy-gold text-savvy-dark hover:bg-savvy-gold/90">
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Visit savvyanalytics.info
                </Button>
                <Button variant="outline" className="border-white text-white hover:bg-white/10">
                  Schedule a Consultation
                </Button>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default SavvyAnalytics;