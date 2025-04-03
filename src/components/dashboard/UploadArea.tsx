
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const UploadArea = ({ onFileUpload }: { onFileUpload: (file: File) => void }) => {
  const [dragActive, setDragActive] = useState(false);
  const [pastedData, setPastedData] = useState('');
  
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onFileUpload(e.target.files[0]);
    }
  };

  const handlePastedDataChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setPastedData(e.target.value);
  };

  const handlePastedDataSubmit = () => {
    if (pastedData.trim()) {
      // Convert pasted data to a file for processing
      const blob = new Blob([pastedData], { type: 'text/plain' });
      const file = new File([blob], 'pasted-data.txt', { type: 'text/plain' });
      onFileUpload(file);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Upload Your Data</CardTitle>
        <CardDescription>
          Upload a file or paste your data to begin cleaning and analysis.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="upload">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="upload">Upload File</TabsTrigger>
            <TabsTrigger value="paste">Paste Data</TabsTrigger>
          </TabsList>
          
          <TabsContent value="upload" className="mt-4">
            <div 
              className={`border-2 border-dashed rounded-lg p-8 text-center ${
                dragActive ? 'border-savvy-blue bg-savvy-blue/5' : 'border-border'
              }`}
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
            >
              <div className="flex flex-col items-center justify-center space-y-4">
                <div className="rounded-full bg-savvy-blue/10 p-3">
                  <svg className="h-6 w-6 text-savvy-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <div className="space-y-1 text-center">
                  <p className="text-sm text-muted-foreground">
                    Drag and drop your file here, or
                  </p>
                  <label className="cursor-pointer text-sm font-medium text-savvy-blue hover:text-savvy-blue/90">
                    <span>browse files</span>
                    <input
                      type="file"
                      className="sr-only"
                      onChange={handleFileChange}
                      accept=".csv,.json,.xlsx,.xml,.txt,.xls,.pdf"
                    />
                  </label>
                </div>
                <p className="text-xs text-muted-foreground">
                  Supported formats: CSV, JSON, XLSX, XLS, XML, TXT, PDF
                </p>
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="paste" className="mt-4">
            <div className="space-y-4">
              <textarea
                className="w-full h-40 p-3 border rounded-md focus:outline-none focus:ring-2 focus:ring-savvy-blue/50"
                placeholder="Paste your data here (CSV, JSON, raw text, etc.)"
                value={pastedData}
                onChange={handlePastedDataChange}
              />
              <Button 
                className="w-full bg-savvy-blue hover:bg-savvy-blue/90"
                onClick={handlePastedDataSubmit}
                disabled={!pastedData.trim()}
              >
                Analyze Pasted Data
              </Button>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default UploadArea;
