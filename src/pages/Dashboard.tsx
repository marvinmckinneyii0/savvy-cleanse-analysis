import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import UploadArea from '@/components/dashboard/UploadArea';
import CleaningPreview from '@/components/dashboard/CleaningPreview';
import AnalysisTypeSelector from '@/components/dashboard/AnalysisTypeSelector';
import AnalysisResults from '@/components/dashboard/AnalysisResults';
import AnalyticsModelsTest from '@/components/dashboard/AnalyticsModelsTest';
import EnhancedDashboard from '@/components/dashboard/EnhancedDashboard';
import LiveDataStream from '@/components/dashboard/LiveDataStream';
import ApiEndpointInfo from '@/components/dashboard/ApiEndpointInfo';
import ApiKeyManager from '@/components/dashboard/ApiKeyManager';
import UserDashboard from '@/components/dashboard/UserDashboard';
import AdminDashboard from '@/components/dashboard/AdminDashboard';
import { ThemeSwitcher } from '@/components/ThemeSwitcher';
import { ParsedData } from '@/utils/fileParser';

const Dashboard = () => {
  const isAdmin = true; // Remove auth check - make admin features accessible
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [cleanedData, setCleanedData] = useState<any | null>(null);
  const [selectedAnalysisType, setSelectedAnalysisType] = useState<string | null>(null);
  
  const handleFileUpload = (file: File, parsedData?: ParsedData) => {
    setSelectedFile(file);
    setSelectedAnalysisType(null);
    
    // Check if it's a file type that doesn't need cleaning (like PDF) or if we have parsed data
    const fileExtension = file.name.split('.').pop()?.toLowerCase();
    if (fileExtension === 'pdf' || parsedData) {
      // For PDFs or files with parsed data, pass them directly to analysis
      setCleanedData(parsedData || { fileType: 'pdf', rawFile: file });
    } else {
      // For other file types, still go through cleaning process
      setCleanedData(null);
    }
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
        <div className="fixed top-4 right-4 z-50 flex items-center gap-2">
          <ThemeSwitcher />
        </div>
        <div className="flex-1 space-y-4 p-4 md:p-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Analytics Dashboard</h1>
              <p className="text-muted-foreground">
                Upload, clean, and analyze your data - now with real-time monitoring
              </p>
            </div>
            <div className="flex items-center">
              <img 
                src="/lovable-uploads/bce4ab85-e6f8-4810-9883-f33ee1cfb90d.png" 
                alt="Savvy Analytics Logo" 
                className="w-8 h-8 mr-2"
              />
            </div>
          </div>

          <Tabs defaultValue="overview" className="w-full">
            <TabsList className={`grid w-full ${isAdmin ? 'grid-cols-6' : 'grid-cols-5'}`}>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="enhanced">Enhanced Analytics</TabsTrigger>
              <TabsTrigger value="file-upload">File Upload & Analysis</TabsTrigger>
              <TabsTrigger value="live-data">Live Data Stream</TabsTrigger>
              <TabsTrigger value="api-keys">API Keys</TabsTrigger>
              {isAdmin && <TabsTrigger value="admin">Admin</TabsTrigger>}
            </TabsList>
            
            <TabsContent value="overview" className="space-y-6">
              <UserDashboard />
            </TabsContent>
            
            <TabsContent value="enhanced" className="space-y-6">
              <EnhancedDashboard />
            </TabsContent>
            
            <TabsContent value="file-upload" className="space-y-6">
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
            </TabsContent>
            
            <TabsContent value="live-data" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <LiveDataStream />
                <ApiEndpointInfo />
              </div>
            </TabsContent>

            <TabsContent value="api-keys" className="space-y-6">
              <ApiKeyManager />
            </TabsContent>

            {isAdmin && (
              <TabsContent value="admin" className="space-y-6">
                <AdminDashboard />
              </TabsContent>
            )}
          </Tabs>
        </div>
      </div>
  );
};

export default Dashboard;
