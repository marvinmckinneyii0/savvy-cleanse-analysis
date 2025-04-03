
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import UploadArea from '@/components/dashboard/UploadArea';
import CleaningPreview from '@/components/dashboard/CleaningPreview';
import AnalysisTypeSelector from '@/components/dashboard/AnalysisTypeSelector';
import AnalysisResults from '@/components/dashboard/AnalysisResults';
import AnalyticsModelsTest from '@/components/dashboard/AnalyticsModelsTest';

const Dashboard = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [cleanedData, setCleanedData] = useState<any | null>(null);
  const [selectedAnalysisType, setSelectedAnalysisType] = useState<string | null>(null);
  
  const handleFileUpload = (file: File) => {
    setSelectedFile(file);
    setCleanedData(null);
    setSelectedAnalysisType(null);
  };
  
  const handleCleaningComplete = (data: any) => {
    setCleanedData(data);
  };
  
  const handleReset = () => {
    setSelectedFile(null);
    setCleanedData(null);
    setSelectedAnalysisType(null);
  };

  return (
    <div className="flex min-h-screen bg-background">
      <div className="flex-1 space-y-4 p-4 md:p-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Analytics Dashboard</h1>
            <p className="text-muted-foreground">
              Upload, clean, and analyze your data
            </p>
          </div>
        </div>

        {!selectedFile && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <UploadArea onFileUpload={handleFileUpload} />
            <AnalyticsModelsTest />
          </div>
        )}

        {selectedFile && !cleanedData && (
          <CleaningPreview 
            file={selectedFile}
            onCleaningComplete={handleCleaningComplete}
            onReset={handleReset}
          />
        )}

        {cleanedData && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Select Analysis Type</h2>
              <Button 
                variant="outline" 
                onClick={handleReset}
                className="text-xs"
              >
                Upload New Data
              </Button>
            </div>
            
            <AnalysisTypeSelector
              selectedType={selectedAnalysisType}
              onSelect={(type) => setSelectedAnalysisType(type)}
            />
            
            {selectedAnalysisType && (
              <AnalysisResults 
                analysisType={selectedAnalysisType} 
                data={cleanedData}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
