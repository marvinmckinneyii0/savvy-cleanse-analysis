
import React from 'react';

const AnalysisTypes = () => {
  const analysisTypes = [
    {
      type: 'Descriptive',
      question: 'What happened?',
      description: 'Summarize historical data with statistics and visualizations.',
      formula: 'μ = Σx / n',
      features: ['Summary statistics', 'Frequency distributions', 'Data visualizations']
    },
    {
      type: 'Diagnostic',
      question: 'Why did it happen?',
      description: 'Identify patterns, correlations, and potential causes.',
      formula: 'r = Σ[(xᵢ - x̄)(yᵢ - ȳ)] / √[Σ(xᵢ - x̄)²Σ(yᵢ - ȳ)²]',
      features: ['Correlation analysis', 'Hypothesis testing', 'Causal inference flags']
    },
    {
      type: 'Predictive',
      question: 'What is likely to happen?',
      description: 'Forecast future trends and outcomes using models.',
      formula: 'ŷ = β₀ + β₁X',
      features: ['Forecasting models', 'Classification algorithms', 'Model performance metrics']
    },
    {
      type: 'Prescriptive',
      question: 'What should we do about it?',
      description: 'Optimize decisions with actionable recommendations.',
      formula: 'Max Z = c₁x₁ + c₂x₂ …',
      features: ['Optimization models', 'Decision trees', 'Scenario simulation']
    }
  ];

  return (
    <section className="py-16 bg-savvy-white" id="analysis-types">
      <div className="container px-4 md:px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold">Four Types of Analytics</h2>
          <p className="text-muted-foreground mt-3 max-w-2xl mx-auto">
            From understanding what happened to determining what actions to take, SavvyClean guides you through the complete analytics journey.
          </p>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
          {analysisTypes.map((analysis, index) => (
            <div key={analysis.type} className={`bg-white dark:bg-card p-4 md:p-6 rounded-lg border shadow-sm hover:shadow-md transition-shadow animate-bounce-in [animation-delay:${index * 100}ms]`}>
              <div className="text-savvy-blue font-semibold mb-2">{analysis.type}</div>
              <h3 className="text-xl font-bold mb-2">{analysis.question}</h3>
              <p className="text-muted-foreground text-sm mb-4">{analysis.description}</p>
              <div className="formula-block mb-4">
                <code className="formula text-savvy-midnight">{analysis.formula}</code>
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
