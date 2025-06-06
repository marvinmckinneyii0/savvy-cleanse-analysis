
import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Copy, Code, Info, Key } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

const ApiEndpointInfo: React.FC = () => {
  const { toast } = useToast();

  const apiEndpoint = `${window.location.origin}/api/live-data`;
  const samplePayload = {
    timestamp: "2024-01-01T12:00:00Z",
    source: "sensor-001",
    metrics: {
      temperature: 23.5,
      humidity: 65,
      pressure: 1013.25
    }
  };

  const curlExample = `curl -X POST ${apiEndpoint} \\
  -H "Content-Type: application/json" \\
  -H "x-api-key: sk_your_api_key_here" \\
  -d '${JSON.stringify(samplePayload, null, 2)}'`;

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied!",
      description: `${label} copied to clipboard`,
    });
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Code className="h-5 w-5" />
          <CardTitle>API Endpoint</CardTitle>
          <Badge variant="outline">REST API</Badge>
        </div>
        <CardDescription>
          Send real-time data to your application
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            Create an API key in the API Keys tab, then use this endpoint to send real-time JSON data. 
            Data will appear instantly in the Live Data Stream.
          </AlertDescription>
        </Alert>

        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">Endpoint URL</label>
            <div className="flex items-center gap-2 mt-1">
              <code className="flex-1 p-2 bg-muted rounded text-sm font-mono">
                POST {apiEndpoint}
              </code>
              <Button
                variant="outline"
                size="sm"
                onClick={() => copyToClipboard(apiEndpoint, "Endpoint URL")}
              >
                <Copy className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium">Required Headers</label>
            <div className="mt-1 space-y-1">
              <code className="block p-2 bg-muted rounded text-sm">
                Content-Type: application/json
              </code>
              <div className="flex items-center gap-2">
                <code className="flex-1 p-2 bg-muted rounded text-sm">
                  x-api-key: sk_your_api_key_here
                </code>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => copyToClipboard("x-api-key: sk_your_api_key_here", "API key header")}
                >
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium">Sample Payload</label>
            <div className="flex items-start gap-2 mt-1">
              <pre className="flex-1 p-2 bg-muted rounded text-sm overflow-x-auto">
                {JSON.stringify(samplePayload, null, 2)}
              </pre>
              <Button
                variant="outline"
                size="sm"
                onClick={() => copyToClipboard(JSON.stringify(samplePayload, null, 2), "Sample payload")}
              >
                <Copy className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium">cURL Example</label>
            <div className="flex items-start gap-2 mt-1">
              <pre className="flex-1 p-2 bg-muted rounded text-sm overflow-x-auto">
                {curlExample}
              </pre>
              <Button
                variant="outline"
                size="sm"
                onClick={() => copyToClipboard(curlExample, "cURL example")}
              >
                <Copy className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <Alert>
            <AlertDescription>
              <strong>Security:</strong> Each user has their own API keys and can only access their own data<br/>
              <strong>Rate limit:</strong> 100 requests per minute per API key<br/>
              <strong>Payload limit:</strong> Maximum 100KB per request
            </AlertDescription>
          </Alert>
        </div>
      </CardContent>
    </Card>
  );
};

export default ApiEndpointInfo;
