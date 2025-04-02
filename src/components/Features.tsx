
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const Features = () => {
  const features = [
    {
      title: 'Smart Data Cleaning',
      description: 'AI-powered cleaning for structured and unstructured data with automatic detection of issues and intelligent transformations.'
    },
    {
      title: 'Python Integration',
      description: 'Native code snippet generator with pandas, NumPy, and scikit-learn support. Download as Jupyter notebook for further analysis.'
    },
    {
      title: 'Guided Analytics',
      description: 'Interactive analysis workflow with smart prompts to refine your goals and deliver actionable insights.'
    },
    {
      title: 'Beautiful Visualizations',
      description: 'Automatic generation of charts, plots, and dashboards tailored to your data and analysis type.'
    },
    {
      title: 'Formula Transparency',
      description: 'See the math behind the results with clear formulas and methodology explanations for full transparency.'
    },
    {
      title: 'Export & Sharing',
      description: 'Export cleaned data, Python code, and complete analysis results for collaboration and further work.'
    }
  ];

  return (
    <section className="py-16 bg-white" id="features">
      <div className="container px-4 md:px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold">Key Features</h2>
          <p className="text-muted-foreground mt-3 max-w-2xl mx-auto">
            Designed to help you clean, transform, and analyze data with power and transparency.
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <Card key={index} className="shadow-sm hover:shadow-md transition-shadow">
              <CardHeader>
                <CardTitle>{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;
