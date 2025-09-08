import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import { BookOpen, Play, Upload, BarChart3, Download, Code } from 'lucide-react';

const Documentation = () => {
  const quickStartSteps = [
    {
      icon: <Upload className="h-6 w-6 text-savvy-blue" />,
      title: "1. Sign in with Google",
      description: "Quick and secure authentication using your Google account"
    },
    {
      icon: <BarChart3 className="h-6 w-6 text-savvy-gold" />,
      title: "2. Upload CSV or Excel",
      description: "Drag and drop your data file or click to browse"
    },
    {
      icon: <Play className="h-6 w-6 text-savvy-blue" />,
      title: "3. Choose analysis type",
      description: "Select from descriptive, diagnostic, predictive, or prescriptive"
    },
    {
      icon: <Download className="h-6 w-6 text-savvy-gold" />,
      title: "4. View dashboard & export",
      description: "Explore results and download cleaned data or Python code"
    }
  ];

  const codeExamples = [
    {
      title: "Upload Dataset",
      description: "Upload your dataset to SavvyClean",
      code: `curl -F "file=@data.csv" \\
     -H "Authorization: Bearer YOUR_API_KEY" \\
     http://localhost:8000/upload`
    },
    {
      title: "Run Cleaning",
      description: "Clean your data with intelligent algorithms",
      code: `curl -F "file=@data.csv" \\
     -H "Authorization: Bearer YOUR_API_KEY" \\
     http://localhost:8000/clean`
    }
  ];

  const sections = [
    {
      title: "Getting Started",
      items: [
        "Account Setup",
        "First Upload",
        "Understanding Results",
        "Exporting Data"
      ]
    },
    {
      title: "Data Cleaning",
      items: [
        "Handling Missing Values",
        "Duplicate Detection",
        "Outlier Analysis",
        "Data Validation"
      ]
    },
    {
      title: "Analytics Types",
      items: [
        "Descriptive Analytics",
        "Diagnostic Analytics", 
        "Predictive Modeling",
        "Prescriptive Insights"
      ]
    },
    {
      title: "Advanced Features",
      items: [
        "Python Integration",
        "Custom Transformations",
        "Batch Processing",
        "API Integration"
      ]
    }
  ];

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <main className="flex-grow">
        {/* Hero Section */}
        <section className="py-16 bg-gradient-to-br from-savvy-dark via-savvy-midnight to-savvy-slate text-white">
          <div className="container px-4 md:px-6">
            <div className="text-center max-w-4xl mx-auto">
              <BookOpen className="h-16 w-16 text-savvy-gold mx-auto mb-6" />
              <h1 className="text-4xl md:text-5xl font-bold mb-6">
                Documentation
                <span className="text-savvy-gold"> & Guides</span>
              </h1>
              <p className="text-xl text-gray-300 max-w-2xl mx-auto">
                Everything you need to get started with SavvyClean and master data analytics workflows.
              </p>
            </div>
          </div>
        </section>

        {/* Quick Start */}
        <section className="py-16 bg-white dark:bg-savvy-dark">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">Quick Start Guide</h2>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                Get up and running with SavvyClean in just 4 simple steps.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
              {quickStartSteps.map((step, index) => (
                <Card key={index} className="text-center shadow-sm hover:shadow-lg transition-all duration-300">
                  <CardHeader>
                    <div className="w-12 h-12 bg-gradient-to-r from-savvy-blue/20 to-savvy-gold/20 rounded-full flex items-center justify-center mx-auto mb-4">
                      {step.icon}
                    </div>
                    <CardTitle className="text-lg">{step.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground text-sm">{step.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* API Examples */}
        <section className="py-16 bg-gradient-to-r from-savvy-blue/5 to-savvy-gold/5">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">API Examples</h2>
              <p className="text-muted-foreground">
                Quick code examples to get you started with the SavvyClean API.
              </p>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-6xl mx-auto">
              {codeExamples.map((example, index) => (
                <Card key={index} className="overflow-hidden">
                  <CardHeader className="bg-savvy-dark text-white">
                    <div className="flex items-center gap-2">
                      <Code className="h-5 w-5" />
                      <CardTitle className="text-lg">{example.title}</CardTitle>
                    </div>
                    <p className="text-gray-300 text-sm">{example.description}</p>
                  </CardHeader>
                  <CardContent className="p-0">
                    <pre className="bg-slate-50 dark:bg-slate-900 p-6 overflow-x-auto text-sm">
                      <code className="text-slate-800 dark:text-slate-200">
                        {example.code}
                      </code>
                    </pre>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Documentation Sections */}
        <section className="py-16 bg-white dark:bg-savvy-dark">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">Documentation Sections</h2>
              <p className="text-muted-foreground">
                Comprehensive guides covering all aspects of SavvyClean.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {sections.map((section, index) => (
                <Card key={index} className="shadow-sm hover:shadow-lg transition-all duration-300">
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <BookOpen className="h-5 w-5 text-savvy-blue" />
                      {section.title}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {section.items.map((item, itemIndex) => (
                        <li key={itemIndex} className="text-sm text-muted-foreground hover:text-savvy-blue cursor-pointer transition-colors">
                          • {item}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Support Section */}
        <section className="py-16 bg-gradient-to-br from-savvy-dark via-savvy-midnight to-savvy-slate text-white">
          <div className="container px-4 md:px-6">
            <div className="text-center max-w-3xl mx-auto">
              <h2 className="text-3xl font-bold mb-4">Need Help?</h2>
              <p className="text-gray-300 mb-8">
                Can't find what you're looking for? Our support team is here to help you succeed.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button className="bg-savvy-gold text-savvy-dark hover:bg-savvy-gold/90">
                  Contact Support
                </Button>
                <Button variant="outline" className="border-white text-white hover:bg-white/10">
                  Join Community
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

export default Documentation;