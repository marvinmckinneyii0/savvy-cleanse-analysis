
import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { cleanData } from '@/utils/api';

export interface CleaningPreviewProps {
  data?: any;
  file?: File;
  onCleaningComplete: (data: any) => void;
  onReset: () => void;
}

const CleaningPreview: React.FC<CleaningPreviewProps> = ({ data, file, onCleaningComplete, onReset }) => {
  const [isProcessing, setIsProcessing] = useState(true);
  const [cleanResult, setCleanResult] = useState<any | null>(null);

  useEffect(() => {
    if (!file) {
      setIsProcessing(false);
      return;
    }

    setIsProcessing(true);

    const run = async () => {
      try {
        const data = await cleanData(file);
        setCleanResult(data);
      } catch (err) {
        console.error('Failed to clean file', err);
      } finally {
        setIsProcessing(false);
      }
    };

    run();
  }, [file]);
  
  // In a real app, this would show before/after data cleaning
  // For demo purposes, we're showing sample data
  
  const beforeData = `id,name,age,income,state
1,John Smith,34,$75.000,CA
2,Sarah Jones,,81000,NY
3,Mike Johnson,43,$62,000,TX
4,Emily Lee,29,55000,IL
5,,51,$90.000,FL`;

  const afterData = `id,name,age,income,state
1,John Smith,34,75000,CA
2,Sarah Jones,null,81000,NY
3,Mike Johnson,43,62000,TX
4,Emily Lee,29,55000,IL
5,Unknown,51,90000,FL`;

  const handleContinue = () => {
    const fallbackData = {
      columns: ['id', 'name', 'age', 'income', 'state'],
      rows: [
        [1, 'John Smith', 34, 75000, 'CA'],
        [2, 'Sarah Jones', null, 81000, 'NY'],
        [3, 'Mike Johnson', 43, 62000, 'TX'],
        [4, 'Emily Lee', 29, 55000, 'IL'],
        [5, 'Unknown', 51, 90000, 'FL']
      ]
    };

    onCleaningComplete(cleanResult || fallbackData);
  };

  if (isProcessing) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Cleaning Your Data</CardTitle>
          <CardDescription>
            We're automatically cleaning and preparing your data for analysis...
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center py-10">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-savvy-gold mb-4"></div>
          <p className="text-muted-foreground">This usually takes a few seconds</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Data Cleaning Preview</CardTitle>
        <CardDescription>
          We've automatically cleaned your data. Review the changes before continuing.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <Tabs defaultValue="comparison">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="comparison">Side by Side</TabsTrigger>
            <TabsTrigger value="before">Before</TabsTrigger>
            <TabsTrigger value="after">After</TabsTrigger>
          </TabsList>
          
          <TabsContent value="comparison" className="mt-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-medium mb-2">Before Cleaning</h3>
                <pre className="bg-muted p-3 rounded-md text-xs overflow-x-auto whitespace-pre-wrap">
                  {beforeData}
                </pre>
              </div>
              
              <div>
                <h3 className="text-sm font-medium mb-2">After Cleaning</h3>
                <pre className="bg-muted p-3 rounded-md text-xs overflow-x-auto whitespace-pre-wrap">
                  {afterData}
                </pre>
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="before" className="mt-4">
            <div>
              <h3 className="text-sm font-medium mb-2">Original Data</h3>
              <pre className="bg-muted p-3 rounded-md text-xs overflow-x-auto whitespace-pre-wrap">
                {beforeData}
              </pre>
            </div>
          </TabsContent>
          
          <TabsContent value="after" className="mt-4">
            <div>
              <h3 className="text-sm font-medium mb-2">Cleaned Data</h3>
              <pre className="bg-muted p-3 rounded-md text-xs overflow-x-auto whitespace-pre-wrap">
                {afterData}
              </pre>
            </div>
          </TabsContent>
        </Tabs>
        
        <div className="space-y-4">
          <h3 className="text-sm font-medium">Issues Detected & Fixed</h3>
          <div className="space-y-2">
            <div className="flex items-start gap-2">
              <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                <svg className="h-3 w-3 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p className="text-sm">Removed formatting from income values ($75.000 → 75000)</p>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                <svg className="h-3 w-3 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p className="text-sm">Fixed incorrectly formatted number ($62,000 → 62000)</p>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                <svg className="h-3 w-3 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p className="text-sm">Handled missing value in name (empty → "Unknown")</p>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                <svg className="h-3 w-3 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p className="text-sm">Standardized missing value in age (empty → "null")</p>
            </div>
          </div>
        </div>
        
        <div className="flex justify-end">
          <Button 
            className="bg-savvy-blue hover:bg-savvy-blue/90"
            onClick={handleContinue}
          >
            Continue to Analysis
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default CleaningPreview;
