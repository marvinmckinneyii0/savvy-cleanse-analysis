
import React from 'react';

const AnalysisTypes = () => {
  const analysisTypes = [
    {
      type: 'Descriptive',
      question: 'What does the data say?',
      description: 'Summarizes each column and shows how key figures change over time and between groups.',
      formula: 'μ = Σx / n',
      features: ['Summary statistics', 'Trends over time', 'Segment comparisons']
    },
    {
      type: 'Quality',
      question: 'What needs a closer look?',
      description: 'Flags data-quality problems and values that sit far from the rest.',
      formula: 'z = (x − μ) / σ',
      features: ['Findings rated by severity', 'Unusual values', 'Recommendations']
    }
  ];

  return (
    <section className="py-16 bg-savvy-white light-surface" id="analysis-types">
      <div className="container px-4 md:px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold">What the Analysis Covers</h2>
          <p className="text-muted-foreground mt-3 max-w-2xl mx-auto">
            Every figure in the report is calculated from your data. AI writes the narrative and never makes up numbers.
          </p>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 md:gap-6 max-w-4xl mx-auto">
          {analysisTypes.map((analysis, index) => (
            <div key={analysis.type} className={`bg-white dark:bg-card p-4 md:p-6 rounded-lg border shadow-sm hover:shadow-md transition-shadow animate-bounce-in [animation-delay:${index * 100}ms]`}>
              <div className="text-savvy-blue font-semibold mb-2">{analysis.type}</div>
              <h3 className="text-xl font-bold mb-2">{analysis.question}</h3>
              <p className="text-muted-foreground text-sm mb-4">{analysis.description}</p>
              <div className="formula-block mb-4">
                <code className="formula text-savvy-midnight dark:text-foreground">{analysis.formula}</code>
              </div>
              <ul className="text-sm space-y-1">
                {analysis.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-savvy-blue"></div>
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default AnalysisTypes;
