import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import { CheckCircle, Code, BarChart3, Eye, FileText, Share2 } from 'lucide-react';

const Features = () => {
  const features = [
    {
      icon: <CheckCircle className="h-8 w-8 text-savvy-gold" />,
      title: 'Data-Quality Checks',
      description: 'SAINT looks for missing values, duplicates, outliers and inconsistent types or formats. Each finding is rated by severity so you can see what matters most.',
    },
    {
      icon: <Code className="h-8 w-8 text-savvy-gold" />,
      title: 'Optional Cleaning',
      description: 'Cleaning is off unless you ask for it. When you do, SAINT applies only supported, rule-based changes to a working copy. Your original file is never changed.',
    },
    {
      icon: <BarChart3 className="h-8 w-8 text-savvy-gold" />,
      title: 'Insights From Your Data',
      description: 'Summary statistics for every column, trends over time, comparisons between segments, and values that sit far from the rest.',
    },
    {
      icon: <Eye className="h-8 w-8 text-savvy-gold" />,
      title: 'A Record of Every Change',
      description: 'Every cleaning action is listed in the report, so you can see exactly what was changed. Findings that need your judgment are flagged and left unchanged.',
    },
    {
      icon: <FileText className="h-8 w-8 text-savvy-gold" />,
      title: 'A Report You Can Read',
      description: 'A plain-language summary with recommendations, delivered as a Word or PDF document. The numbers are computed first; AI only writes the narrative around them.',
    },
    {
      icon: <Share2 className="h-8 w-8 text-savvy-gold" />,
      title: 'Cleaned Data on Request',
      description: 'If you chose cleaning, you get the cleaned CSV back along with the report.',
    },
  ];

  return (
    <div className="flex flex-col min-h-screen" data-page="features">
      <Navbar />
      <main className="flex-grow">
        {/* Hero Section */}
        <section className="py-20 md:py-28 bg-gradient-to-b from-savvy-white to-savvy-gold/5">
          <div className="container px-4 md:px-6">
            <div className="text-center max-w-4xl mx-auto">
              <h1 className="text-3xl md:text-5xl font-bold tracking-tighter mb-6">
                What SAINT Does 
                <span className="text-savvy-gold"> Today</span>
              </h1>
              <p className="text-muted-foreground md:text-xl max-w-2xl mx-auto">
                The concierge beta is a done-for-you service. Here is what the report covers and how cleaning works.
              </p>
            </div>
          </div>
        </section>

        {/* Features Grid */}
        <section className="py-16 bg-white light-surface">
          <div className="container px-4 md:px-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {features.map((feature, index) => (
                <Card key={index} className="shadow-sm hover:shadow-md transition-shadow">
                  <CardHeader>
                    <div className="mb-4">
                      {feature.icon}
                    </div>
                    <CardTitle className="text-xl">{feature.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground leading-relaxed">{feature.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Additional Benefits */}
        <section className="py-16 bg-savvy-slate/5">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">How We Work</h2>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                During the beta, a person runs SAINT on your file and emails you the report.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="w-16 h-16 bg-savvy-gold/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="h-8 w-8 text-savvy-gold" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Computed, Not Guessed</h3>
                <p className="text-muted-foreground">
                  Every figure is calculated from your data. AI writes the narrative and never makes up numbers.
                </p>
              </div>
              
              <div className="text-center">
                <div className="w-16 h-16 bg-savvy-gold/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Code className="h-8 w-8 text-savvy-gold" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Nothing Changed Silently</h3>
                <p className="text-muted-foreground">
                  Your original file stays as you sent it. Cleaning happens only on request, on a copy, with every change recorded.
                </p>
              </div>
              
              <div className="text-center">
                <div className="w-16 h-16 bg-savvy-gold/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <BarChart3 className="h-8 w-8 text-savvy-gold" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Clear About Limits</h3>
                <p className="text-muted-foreground">
                  The beta takes CSV files up to 100 MB. Reports are written documents and do not include charts yet.
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

export default Features;