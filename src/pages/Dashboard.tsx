import React, { useState, useCallback } from 'react';
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
import DatasetManager, { Dataset } from '@/components/dashboard/DatasetManager';
import { ThemeSwitcher } from '@/components/ThemeSwitcher';
import { ParsedData } from '@/utils/fileParser';
import { useToast } from '@/hooks/use-toast';

const Dashboard = () => {
  const isAdmin = true;
  const { toast } = useToast();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [activeDatasetId, setActiveDatasetId] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [cleanedData, setCleanedData] = useState<any | null>(null);
  const [selectedAnalysisType, setSelectedAnalysisType] = useState<string | null>(null);

  const activeDataset = datasets.find(d => d.id === activeDatasetId) ?? null;

  const handleFileUpload = (file: File, parsedData?: ParsedData) => {
    const fileExtension = file.name.split('.').pop()?.toLowerCase();
    const data = parsedData || (fileExtension === 'pdf' ? { fileType: 'pdf', rawFile: file } : null);

    if (data) {
      const newDataset: Dataset = {
        id: crypto.randomUUID(),
        file,
        parsedData: data as ParsedData,
        uploadedAt: new Date(),
      };
      setDatasets(prev => [...prev, newDataset]);
      setActiveDatasetId(newDataset.id);
      setCleanedData(data);
      setSelectedFile(file);
      setSelectedAnalysisType(null);
    } else {
      setSelectedFile(file);
      setCleanedData(null);
      setSelectedAnalysisType(null);
    }
  };

  const handleCleaningComplete = (data: any) => {
    if (selectedFile) {
      const newDataset: Dataset = {
        id: crypto.randomUUID(),
        file: selectedFile,
        parsedData: data as ParsedData,
        uploadedAt: new Date(),
      };
      setDatasets(prev => [...prev, newDataset]);
      setActiveDatasetId(newDataset.id);
    }
    setCleanedData(data);
  };

  const handleSelectDataset = (id: string) => {
    const ds = datasets.find(d => d.id === id);
    if (ds) {
      setActiveDatasetId(id);
      setSelectedFile(ds.file);
      setCleanedData(ds.parsedData);
      setSelectedAnalysisType(null);
    }
  };

  const handleRemoveDataset = (id: string) => {
    setDatasets(prev => prev.filter(d => d.id !== id));
    if (activeDatasetId === id) {
      setActiveDatasetId(null);
      setSelectedFile(null);
      setCleanedData(null);
      setSelectedAnalysisType(null);
    }
    toast({ title: 'Dataset removed' });
  };

  const handleDownloadDataset = useCallback((dataset: Dataset) => {
    const url = URL.createObjectURL(dataset.file);
    const a = document.createElement('a');
    a.href = url;
    a.download = dataset.file.name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast({ title: 'Download started', description: dataset.file.name });
  }, [toast]);

  const handleReset = () => {
    setSelectedFile(null);
    setCleanedData(null);
    setSelectedAnalysisType(null);
    setActiveDatasetId(null);
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
              src="/lovable-uploads/1a5ff488-1ca2-4dda-8f25-3e165a31f539.png"
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
            {/* Dataset Manager - always visible when datasets exist */}
            <DatasetManager
              datasets={datasets}
              activeDatasetId={activeDatasetId}
              onSelect={handleSelectDataset}
              onRemove={handleRemoveDataset}
              onDownload={handleDownloadDataset}
            />

            {/* Upload area - always visible to allow adding more datasets */}
            {!selectedFile || cleanedData ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <UploadArea onFileUpload={handleFileUpload} />
                <AnalyticsModelsTest />
              </div>
            ) : null}

            {/* Cleaning step for files that need it */}
            {selectedFile && !cleanedData && (
              <CleaningPreview
                file={selectedFile}
                onCleaningComplete={handleCleaningComplete}
                onReset={handleReset}
              />
            )}

            {/* Analysis section for active dataset */}
            {cleanedData && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-semibold">
                    Select Analysis Type
                    {activeDataset && (
                      <span className="text-sm font-normal text-muted-foreground ml-2">
                        — {activeDataset.file.name}
                      </span>
                    )}
                  </h2>
                  <Button variant="outline" onClick={handleReset} className="text-xs">
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
