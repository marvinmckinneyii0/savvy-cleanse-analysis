
import React from 'react';
import { Card, CardContent } from '@/components/ui/card';

interface AnalysisType {
  id: string;
  title: string;
  question: string;
  description: string;
  icon: React.ReactNode;
}

interface AnalysisTypeSelectorProps {
  selectedType: string | null;
  onSelect: (type: string) => void;
}

const AnalysisTypeSelector: React.FC<AnalysisTypeSelectorProps> = ({ selectedType, onSelect }) => {
  const analysisTypes: AnalysisType[] = [
    {
      id: 'descriptive',
      title: 'Descriptive',
      question: 'What happened?',
      description: 'Summarize historical data with statistics and visualizations',
      icon: (
        <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
    },
    {
      id: 'diagnostic',
      title: 'Diagnostic',
      question: 'Why did it happen?',
      description: 'Identify patterns, correlations, and potential causes',
      icon: (
        <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      ),
    },
    {
      id: 'predictive',
      title: 'Predictive',
      question: 'What might happen?',
      description: 'Forecast future trends and outcomes using models',
      icon: (
        <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
      id: 'prescriptive',
      title: 'Prescriptive',
      question: 'What should we do?',
      description: 'Optimize decisions with actionable recommendations',
      icon: (
        <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {analysisTypes.map((type) => (
        <Card 
          key={type.id} 
          className={`cursor-pointer transition-all hover:border-savvy-blue ${
            selectedType === type.id ? 'ring-2 ring-savvy-blue border-savvy-blue' : ''
          }`}
          onClick={() => onSelect(type.id)}
        >
          <CardContent className="p-5">
            <div className="flex flex-col items-start space-y-2">
              <div className={`p-2 rounded-md ${
                selectedType === type.id ? 'bg-savvy-blue text-white' : 'bg-muted'
              }`}>
                {type.icon}
              </div>
              <h3 className="font-medium">{type.title}</h3>
              <p className="font-semibold text-sm">{type.question}</p>
              <p className="text-muted-foreground text-sm">{type.description}</p>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default AnalysisTypeSelector;
