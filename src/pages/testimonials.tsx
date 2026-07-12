import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import { Quote, Star } from 'lucide-react';

const Testimonials = () => {
  const testimonials = [
    {
      quote: "SAINT turned our messy CRM exports into usable insights in minutes. What used to take our team hours of manual cleaning now happens automatically. The transparency in methodology gives us confidence in our decisions.",
      author: "Amelia Richardson",
      title: "Product Manager",
      company: "TechFlow Solutions",
      rating: 5,
      initials: "AR",
      category: "Data Cleaning"
    },
    {
      quote: "Finally, a tool that explains the math behind the numbers. Transparency is key in our industry, and SAINT delivers exactly that. The formula explanations and statistical methods are invaluable for our reports.",
      author: "David Thompson",
      title: "Senior Data Analyst",
      company: "Financial Insights Corp",
      rating: 5,
      initials: "DT",
      category: "Analytics"
    },
    {
      quote: "We reduced reporting time by 70% using SAINT's guided analytics. The predictive models are surprisingly accurate, and the Python export feature lets us integrate seamlessly with our existing workflows.",
      author: "Sophia Kumar",
      title: "Operations Lead",
      company: "Supply Chain Dynamics",
      rating: 5,
      initials: "SK",
      category: "Efficiency"
    },
    {
      quote: "The Jupyter notebook export is a game-changer. I can now share reproducible analysis with my team while maintaining the interactive exploration that SAINT provides. It's the best of both worlds.",
      author: "Marcus Chen",
      title: "Research Scientist",
      company: "BioData Labs",
      rating: 5,
      initials: "MC",
      category: "Integration"
    },
    {
      quote: "As a consultant, I need tools that work reliably across different client datasets. SAINT handles everything from survey data to financial records with the same level of sophistication.",
      author: "Elena Vasquez",
      title: "Data Science Consultant",
      company: "Independent",
      rating: 5,
      initials: "EV",
      category: "Versatility"
    },
    {
      quote: "The guided analytics feature is perfect for our non-technical stakeholders. They can run their own analysis without compromising on statistical rigor. It's democratizing data science in our organization.",
      author: "James Wilson",
      title: "Head of Strategy",
      company: "Marketing Innovations Inc",
      rating: 5,
      initials: "JW",
      category: "Accessibility"
    }
  ];

  const stats = [
    { value: "10,000+", label: "Happy Users" },
    { value: "99.9%", label: "Uptime" },
    { value: "4.9/5", label: "Average Rating" },
    { value: "500M+", label: "Rows Processed" }
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
                Trusted by Data Professionals
                <span className="text-savvy-gold"> Worldwide</span>
              </h1>
              <p className="text-xl text-gray-300 max-w-2xl mx-auto">
                See how SAINT is transforming data workflows across industries and helping teams make better decisions faster.
              </p>
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="py-12 bg-white dark:bg-savvy-dark border-b">
          <div className="container px-4 md:px-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
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

        {/* Testimonials Grid */}
        <section className="py-16 bg-gradient-to-r from-savvy-blue/5 to-savvy-gold/5">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">What Our Users Say</h2>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                Real feedback from data professionals who use SAINT to transform their workflows.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {testimonials.map((testimonial, index) => (
                <Card key={index} className="h-full shadow-sm hover:shadow-lg transition-all duration-300">
                  <CardContent className="p-6 h-full flex flex-col">
                    <div className="flex items-start mb-4">
                      <Quote className="h-6 w-6 text-savvy-gold mr-2 flex-shrink-0 mt-1" />
                      <Badge variant="secondary" className="text-xs">
                        {testimonial.category}
                      </Badge>
                    </div>
                    
                    <div className="flex mb-4">
                      {[...Array(testimonial.rating)].map((_, i) => (
                        <Star key={i} className="h-4 w-4 text-yellow-400 fill-current" />
                      ))}
                    </div>
                    
                    <blockquote className="text-muted-foreground mb-6 flex-grow leading-relaxed">
                      "{testimonial.quote}"
                    </blockquote>
                    
                    <div className="flex items-center mt-auto">
                      <Avatar className="h-10 w-10 mr-3">
                        <AvatarFallback className="bg-savvy-blue text-white">
                          {testimonial.initials}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <div className="font-semibold text-sm">{testimonial.author}</div>
                        <div className="text-xs text-muted-foreground">
                          {testimonial.title}, {testimonial.company}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-16 bg-white dark:bg-savvy-dark">
          <div className="container px-4 md:px-6">
            <div className="text-center max-w-3xl mx-auto">
              <h2 className="text-3xl font-bold mb-4">Join Thousands of Satisfied Users</h2>
              <p className="text-muted-foreground mb-8">
                Start your free trial today and see why data professionals choose SAINT for their analytics needs.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <button className="bg-savvy-blue text-white px-8 py-3 rounded-lg hover:bg-savvy-blue/90 transition-colors">
                  Start Free Trial
                </button>
                <button className="border border-savvy-gold text-savvy-gold px-8 py-3 rounded-lg hover:bg-savvy-gold/10 transition-colors">
                  View Pricing
                </button>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default Testimonials;