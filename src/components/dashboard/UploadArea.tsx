
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Upload, AlertCircle } from 'lucide-react';
import { parseFile, ParsedData } from '@/utils/fileParser';
import DataPreview from './DataPreview';

interface UploadAreaProps {
  onFileUpload: (file: File, parsedData?: ParsedData) => void;
}

const UploadArea: React.FC<UploadAreaProps> = ({ onFileUpload }) => {
  const [dragActive, setDragActive] = useState(false);
  const [pastedData, setPastedData] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [parsedData, setParsedData] = useState<ParsedData | null>(null);
  const [fileName, setFileName] = useState<string>('');
  
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
      handleFileProcessing(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileProcessing(e.target.files[0]);
    }
  };

  const handleFileProcessing = async (file: File) => {
    setIsLoading(true);
    setError(null);
    setParsedData(null);
    setFileName(file.name);

    const supportedExtensions = ['csv', 'json', 'xls', 'xlsx', 'xml', 'txt', 'pdf'];
    const fileExtension = file.name.split('.').pop()?.toLowerCase();
    
    if (!fileExtension || !supportedExtensions.includes(fileExtension)) {
      setError(`Unsupported file format. Please upload: ${supportedExtensions.join(', ').toUpperCase()}`);
      setIsLoading(false);
      return;
    }

    try {
      const result = await parseFile(file);
      
      if (result.success && result.data) {
        setParsedData(result.data);
        onFileUpload(file, result.data);
      } else {
        setError(result.error || 'Failed to parse file');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePastedDataChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setPastedData(e.target.value);
    setError(null);
  };

  const handlePastedDataSubmit = async () => {
    if (!pastedData.trim()) {
      setError('Please paste some data before submitting');
      return;
    }

    setIsLoading(true);
    setError(null);
    setParsedData(null);

    try {
      // Create a blob from pasted data and treat as text file
      const blob = new Blob([pastedData], { type: 'text/plain' });
      const file = new File([blob], 'pasted-data.txt', { type: 'text/plain' });
      
      const result = await parseFile(file);
      
      if (result.success && result.data) {
        setParsedData(result.data);
        setFileName('pasted-data.txt');
        onFileUpload(file, result.data);
      } else {
        setError(result.error || 'Failed to parse pasted data');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const resetUpload = () => {
    setParsedData(null);
    setError(null);
    setFileName('');
    setPastedData('');
  };

  if (parsedData) {
    return (
      <div className="w-full space-y-4">
        <DataPreview data={parsedData} fileName={fileName} />
        <Button 
          variant="outline" 
          onClick={resetUpload}
          className="w-full"
        >
          Upload Different File
        </Button>
      </div>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Upload Your Data</CardTitle>
        <CardDescription>
          Upload a file or paste your data to begin cleaning and analysis.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <Tabs defaultValue="upload">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="upload">Upload File</TabsTrigger>
            <TabsTrigger value="paste">Paste Data</TabsTrigger>
          </TabsList>
          
          <TabsContent value="upload" className="mt-4">
            <div 
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                dragActive ? 'border-savvy-gold bg-savvy-gold/5' : 'border-border'
              } ${isLoading ? 'opacity-50 pointer-events-none' : ''}`}
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
            >
              <div className="flex flex-col items-center justify-center space-y-4">
                <div className="rounded-full bg-savvy-gold/10 p-3">
                  {isLoading ? (
                    <Loader2 className="h-6 w-6 text-savvy-gold animate-spin" />
                  ) : (
                    <Upload className="h-6 w-6 text-savvy-gold" />
                  )}
                </div>
                <div className="space-y-1 text-center">
                  <p className="text-sm text-muted-foreground">
                    {isLoading ? 'Processing file...' : 'Drag and drop your file here, or'}
                  </p>
                  {!isLoading && (
                    <label className="cursor-pointer text-sm font-medium text-savvy-gold hover:text-savvy-gold/90">
                      <span>browse files</span>
                      <input
                        type="file"
                        className="sr-only"
                        onChange={handleFileChange}
                        accept=".csv,.json,.xlsx,.xml,.txt,.xls,.pdf"
                        disabled={isLoading}
                      />
                    </label>
                  )}
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
                className="w-full h-40 p-3 border rounded-md focus:outline-none focus:ring-2 focus:ring-savvy-gold/50 resize-none"
                placeholder="Paste your data here (CSV, JSON, raw text, etc.)"
                value={pastedData}
                onChange={handlePastedDataChange}
                disabled={isLoading}
              />
              <Button 
                className="w-full bg-savvy-gold hover:bg-savvy-gold/90"
                onClick={handlePastedDataSubmit}
                disabled={!pastedData.trim() || isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  'Analyze Pasted Data'
                )}
              </Button>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default UploadArea;
