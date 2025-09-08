import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import { Code, Database, Zap, Shield, Globe, Cpu } from 'lucide-react';

const API = () => {
  const features = [
    {
      icon: <Code className="h-6 w-6 text-savvy-blue" />,
      title: "RESTful Design",
      description: "Clean, intuitive REST API following industry standards"
    },
    {
      icon: <Database className="h-6 w-6 text-savvy-gold" />,
      title: "Multiple Formats",
      description: "Support for CSV, JSON, Excel, and more data formats"
    },
    {
      icon: <Zap className="h-6 w-6 text-savvy-blue" />,
      title: "Real-time Processing",
      description: "Instant data cleaning and analysis with webhook support"
    },
    {
      icon: <Shield className="h-6 w-6 text-savvy-gold" />,
      title: "Secure & Reliable",
      description: "Enterprise-grade security with 99.9% uptime SLA"
    },
    {
      icon: <Globe className="h-6 w-6 text-savvy-blue" />,
      title: "Global CDN",
      description: "Fast response times worldwide with edge computing"
    },
    {
      icon: <Cpu className="h-6 w-6 text-savvy-gold" />,
      title: "Auto-scaling",
      description: "Handle any workload from small datasets to enterprise scale"
    }
  ];

  const codeExample = `# Upload and clean data with SavvyClean API
import requests

# Upload dataset
response = requests.post(
    'https://api.savvyclean.com/v1/upload',
    files={'file': open('data.csv', 'rb')},
    headers={'Authorization': 'Bearer YOUR_API_KEY'}
)
dataset_id = response.json()['dataset_id']

# Run cleaning pipeline
clean_response = requests.post(
    f'https://api.savvyclean.com/v1/datasets/{dataset_id}/clean',
    json={
        'operations': ['remove_duplicates', 'handle_missing', 'detect_outliers'],
        'options': {'missing_strategy': 'median'}
    },
    headers={'Authorization': 'Bearer YOUR_API_KEY'}
)

# Get cleaned data
cleaned_data = requests.get(
    f'https://api.savvyclean.com/v1/datasets/{dataset_id}/export',
    headers={'Authorization': 'Bearer YOUR_API_KEY'}
)`;

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <main className="flex-grow">
        {/* Hero Section */}
        <section className="py-16 bg-gradient-to-br from-savvy-dark via-savvy-midnight to-savvy-slate text-white">
          <div className="container px-4 md:px-6">
            <div className="text-center max-w-4xl mx-auto">
              <Badge className="mb-4 bg-savvy-gold/20 text-savvy-gold border-savvy-gold/30">
                Private Beta
              </Badge>
              <h1 className="text-4xl md:text-5xl font-bold mb-6">
                SavvyClean
                <span className="text-savvy-gold"> API</span>
              </h1>
              <p className="text-xl text-gray-300 max-w-2xl mx-auto mb-8">
                Integrate powerful data cleaning and analytics capabilities directly into your applications with our developer-friendly API.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button className="bg-savvy-blue hover:bg-savvy-blue/90">
                  Request Beta Access
                </Button>
                <Button variant="outline" className="border-savvy-gold text-savvy-gold hover:bg-savvy-gold/10">
                  View Documentation
                </Button>
              </div>
            </div>
          </div>
        </section>

        {/* Features Grid */}
        <section className="py-16 bg-white dark:bg-savvy-dark">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">API Features</h2>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                Built for developers who need reliable, scalable data processing capabilities.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {features.map((feature, index) => (
                <Card key={index} className="shadow-sm hover:shadow-lg transition-all duration-300">
                  <CardHeader>
                    <div className="flex items-center gap-3">
                      {feature.icon}
                      <CardTitle className="text-lg">{feature.title}</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground">{feature.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Code Example */}
        <section className="py-16 bg-gradient-to-r from-savvy-blue/5 to-savvy-gold/5">
          <div className="container px-4 md:px-6">
            <div className="max-w-4xl mx-auto">
              <div className="text-center mb-8">
                <h2 className="text-3xl font-bold mb-4">Quick Start Example</h2>
                <p className="text-muted-foreground">
                  Get started with just a few lines of code. Clean and analyze your data programmatically.
                </p>
              </div>
              
              <Card className="overflow-hidden">
                <CardHeader className="bg-savvy-dark text-white">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">Python Example</CardTitle>
                    <Badge className="bg-savvy-gold text-savvy-dark">
                      Coming Soon
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <pre className="bg-slate-50 dark:bg-slate-900 p-6 overflow-x-auto text-sm">
                    <code className="text-slate-800 dark:text-slate-200">
                      {codeExample}
                    </code>
                  </pre>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* API Endpoints Preview */}
        <section className="py-16 bg-white dark:bg-savvy-dark">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">API Endpoints</h2>
              <p className="text-muted-foreground">
                SavvyClean API is in private beta. Here's a preview of the planned endpoints:
              </p>
            </div>
            
            <div className="max-w-4xl mx-auto space-y-4">
              {[
                { method: 'POST', endpoint: '/upload', description: 'Upload dataset for processing' },
                { method: 'POST', endpoint: '/clean', description: 'Run data cleaning operations' },
                { method: 'POST', endpoint: '/analyze/descriptive', description: 'Generate descriptive statistics' },
                { method: 'POST', endpoint: '/analyze/diagnostic', description: 'Perform diagnostic analysis' },
                { method: 'POST', endpoint: '/analyze/predictive', description: 'Run predictive models' },
                { method: 'POST', endpoint: '/analyze/prescriptive', description: 'Generate prescriptive insights' },
                { method: 'POST', endpoint: '/analyze/nlp', description: 'Natural language processing' },
                { method: 'GET', endpoint: '/export/*', description: 'Export processed data and results' },
                { method: 'GET', endpoint: '/dashboard/*', description: 'Access dashboard data' }
              ].map((endpoint, index) => (
                <Card key={index} className="shadow-sm">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <Badge 
                          variant={endpoint.method === 'GET' ? 'secondary' : 'default'}
                          className={endpoint.method === 'GET' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'}
                        >
                          {endpoint.method}
                        </Badge>
                        <code className="text-sm font-mono">{endpoint.endpoint}</code>
                      </div>
                      <span className="text-muted-foreground text-sm">{endpoint.description}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-16 bg-gradient-to-br from-savvy-dark via-savvy-midnight to-savvy-slate text-white">
          <div className="container px-4 md:px-6">
            <div className="text-center max-w-3xl mx-auto">
              <h2 className="text-3xl font-bold mb-4">Ready to Get Started?</h2>
              <p className="text-gray-300 mb-8">
                Join our private beta and be among the first to experience the power of SavvyClean API.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button className="bg-savvy-gold text-savvy-dark hover:bg-savvy-gold/90">
                  Request Beta Access
                </Button>
                <Button variant="outline" className="border-white text-white hover:bg-white/10">
                  Join Waitlist
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

export default API;