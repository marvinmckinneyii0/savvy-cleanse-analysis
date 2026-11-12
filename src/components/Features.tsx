
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const Features = () => {
  const features = [
    {
      title: 'Data-Quality Checks',
      description: 'Finds missing values, duplicates, outliers and inconsistent types or formats, and rates each finding by severity.'
    },
    {
      title: 'Optional Cleaning',
      description: 'Cleaning is off unless you ask for it. When you do, SAINT applies only supported, rule-based changes to a working copy and keeps your original file unchanged.'
    },
    {
      title: 'A Record of Every Change',
      description: 'Every cleaning action is listed in the report. Findings that need your judgment are flagged and left unchanged.'
    },
    {
      title: 'Insights From Your Data',
      description: 'Summary statistics, trends over time, comparisons between segments and unusual values, computed directly from your file.'
    },
    {
      title: 'A Report You Can Read',
      description: 'A written summary with recommendations, delivered as a Word (.docx) document. The numbers are computed first; any AI-assisted narrative uses those results.'
    },
    {
      title: 'Cleaned Data on Request',
      description: 'If you chose cleaning, you get the cleaned CSV back along with the report.'
    }
  ];

  return (
    <section className="py-16 bg-white light-surface" id="features">
      <div className="container px-4 md:px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold">Key Features</h2>
          <p className="text-muted-foreground mt-3 max-w-2xl mx-auto">
            What the concierge beta delivers today.
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
