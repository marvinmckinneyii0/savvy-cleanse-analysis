
import React, { useState } from 'react';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import UploadArea from '@/components/dashboard/UploadArea';
import CleaningPreview from '@/components/dashboard/CleaningPreview';
import AnalysisTypeSelector from '@/components/dashboard/AnalysisTypeSelector';
import AnalysisResults from '@/components/dashboard/AnalysisResults';

// Flow states
type FlowState = 'upload' | 'cleaning' | 'analysis-selection' | 'results';

const Dashboard = () => {
  const [flowState, setFlowState] = useState<FlowState>('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedAnalysisType, setSelectedAnalysisType] = useState<string | null>(null);
  
  const handleFileUpload = (file: File) => {
    setSelectedFile(file);
    setFlowState('cleaning');
    // In a real app, you would process the file here
    console.log('File uploaded:', file.name);
  };
  
  const handleCleaningContinue = () => {
    setFlowState('analysis-selection');
  };
  
  const handleAnalysisTypeSelect = (type: string) => {
    setSelectedAnalysisType(type);
    setFlowState('results');
    // In a real app, you would run the analysis here
    console.log('Analysis type selected:', type);
  };
  
  const renderCurrentStep = () => {
    switch (flowState) {
      case 'upload':
        return <UploadArea onFileUpload={handleFileUpload} />;
      case 'cleaning':
        return <CleaningPreview data={selectedFile} onContinue={handleCleaningContinue} />;
      case 'analysis-selection':
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold">Choose Analysis Type</h2>
            <p className="text-muted-foreground">
              Select the type of analysis you want to perform on your cleaned data.
            </p>
            <AnalysisTypeSelector 
              selectedType={selectedAnalysisType}
              onSelect={handleAnalysisTypeSelect}
            />
          </div>
        );
      case 'results':
        return (
          <AnalysisResults 
            analysisType={selectedAnalysisType || ''} 
            data={selectedFile}
          />
        );
      default:
        return <UploadArea onFileUpload={handleFileUpload} />;
    }
  };
  
  const renderProgressIndicator = () => {
    const steps = [
      { id: 'upload', label: 'Upload' },
      { id: 'cleaning', label: 'Clean' },
      { id: 'analysis-selection', label: 'Select Analysis' },
      { id: 'results', label: 'Results' }
    ];
    
    return (
      <div className="flex items-center justify-center space-x-2 md:space-x-4">
        {steps.map((step, index) => (
          <React.Fragment key={step.id}>
            <div className="flex items-center">
              <div 
                className={`step-indicator ${
                  flowState === step.id 
                    ? 'bg-savvy-blue text-white' 
                    : steps.findIndex(s => s.id === flowState) > index 
                      ? 'bg-green-500 text-white' 
                      : 'bg-muted text-muted-foreground'
                }`}
              >
                {steps.findIndex(s => s.id === flowState) > index ? (
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  index + 1
                )}
              </div>
              <span className="ml-2 hidden md:inline text-sm font-medium">
                {step.label}
              </span>
            </div>
            
            {index < steps.length - 1 && (
              <div 
                className={`h-px w-8 md:w-16 ${
                  steps.findIndex(s => s.id === flowState) > index 
                    ? 'bg-green-500' 
                    : 'bg-muted'
                }`}
              />
            )}
          </React.Fragment>
        ))}
      </div>
    );
  };
  
  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <main className="flex-grow py-8">
        <div className="container px-4 md:px-6">
          <div className="mb-8">
            <h1 className="text-3xl font-bold">SavvyClean Dashboard</h1>
            <p className="text-muted-foreground mt-1">
              Clean, transform, and analyze your data
            </p>
          </div>
          
          <div className="mb-8">
            {renderProgressIndicator()}
          </div>
          
          {renderCurrentStep()}
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Dashboard;
