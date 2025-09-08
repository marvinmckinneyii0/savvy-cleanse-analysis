import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import { CheckCircle, Code, BarChart3, Eye, FileText, Share2 } from 'lucide-react';

const Features = () => {
  const features = [
    {
      icon: <CheckCircle className="h-8 w-8 text-savvy-blue" />,
      title: 'Smart Data Cleaning',
      description: 'Automatically detect missing values, duplicates, and outliers. One-click cleaning for structured and unstructured data. Our advanced algorithms identify data quality issues and suggest intelligent transformations, saving hours of manual work.',
    },
    {
      icon: <Code className="h-8 w-8 text-savvy-gold" />,
      title: 'Python Integration',
      description: 'Export Jupyter notebooks or Python scripts for reproducibility. Generate clean, well-documented code using pandas, NumPy, and scikit-learn. Every analysis comes with executable code that you can modify and extend.',
    },
    {
      icon: <BarChart3 className="h-8 w-8 text-savvy-blue" />,
      title: 'Guided Analytics',
      description: 'Choose from descriptive, diagnostic, predictive, or prescriptive workflows. Our intelligent system guides you through each step, asking the right questions to refine your analysis goals and deliver actionable insights.',
    },
    {
      icon: <Eye className="h-8 w-8 text-savvy-gold" />,
      title: 'Beautiful Visualizations',
      description: 'Generate interactive plots, charts, and dashboards instantly. From simple histograms to complex multi-dimensional visualizations, our system automatically selects the best chart types for your data and analysis objectives.',
    },
    {
      icon: <FileText className="h-8 w-8 text-savvy-blue" />,
      title: 'Formula Transparency',
      description: 'Every result comes with formulas, statistical methods, and p-values. Understand exactly how your insights were generated with clear mathematical explanations, confidence intervals, and methodology documentation.',
    },
    {
      icon: <Share2 className="h-8 w-8 text-savvy-gold" />,
      title: 'Export & Sharing',
      description: 'Share cleaned data, reports, and notebooks securely. Export in multiple formats including CSV, Excel, PDF reports, and interactive HTML dashboards. Collaborate with team members through secure sharing links.',
    },
  ];

  return (
    <div className="flex flex-col min-h-screen" data-page="features">
      <Navbar />
      <main className="flex-grow">
        {/* Hero Section */}
        <section className="py-16 bg-gradient-to-br from-savvy-dark via-savvy-midnight to-savvy-slate text-white">
          <div className="container px-4 md:px-6">
            <div className="text-center max-w-4xl mx-auto">
              <h1 className="text-4xl md:text-5xl font-bold mb-6">
                Powerful Features for 
                <span className="text-savvy-gold"> Data Excellence</span>
              </h1>
              <p className="text-xl text-gray-300 max-w-2xl mx-auto">
                Discover the comprehensive toolkit that makes SavvyClean the preferred choice for data professionals worldwide.
              </p>
            </div>
          </div>
        </section>

        {/* Features Grid */}
        <section className="py-16 bg-white dark:bg-savvy-dark">
          <div className="container px-4 md:px-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {features.map((feature, index) => (
                <Card key={index} className="shadow-sm hover:shadow-lg transition-all duration-300 border-0 bg-card/50 backdrop-blur-sm">
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
        <section className="py-16 bg-gradient-to-r from-savvy-blue/10 to-savvy-gold/10">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">Why Choose SavvyClean?</h2>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                Built by data scientists, for data scientists. Every feature is designed to save time while maintaining the highest standards of analytical rigor.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="w-16 h-16 bg-savvy-blue/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="h-8 w-8 text-savvy-blue" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Quality First</h3>
                <p className="text-muted-foreground">
                  Every algorithm is validated against industry standards and peer-reviewed methodologies.
                </p>
              </div>
              
              <div className="text-center">
                <div className="w-16 h-16 bg-savvy-gold/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Code className="h-8 w-8 text-savvy-gold" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Open & Transparent</h3>
                <p className="text-muted-foreground">
                  No black boxes. Every calculation is documented and exportable as clean Python code.
                </p>
              </div>
              
              <div className="text-center">
                <div className="w-16 h-16 bg-savvy-blue/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <BarChart3 className="h-8 w-8 text-savvy-blue" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Enterprise Ready</h3>
                <p className="text-muted-foreground">
                  Scalable infrastructure with enterprise security and compliance features.
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