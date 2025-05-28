
import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Code, Copy, CheckCircle, Eye, EyeOff } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

const ApiEndpointInfo: React.FC = () => {
  const [showApiKey, setShowApiKey] = useState(false);
  const { toast } = useToast();

  const apiEndpoint = `${window.location.origin}/api/live-data`;
  const samplePayload = {
    timestamp: new Date().toISOString(),
    source: "sensor-001",
    metrics: {
      temperature: 23.5,
      humidity: 65,
      pressure: 1013.25
    }
  };

  const curlExample = `curl -X POST "${apiEndpoint}" \\
  -H "Content-Type: application/json" \\
  -H "x-api-key: YOUR_API_KEY" \\
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
          <CardTitle>API Integration</CardTitle>
        </div>
        <CardDescription>
          Send real-time data to your dashboard using our REST API
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label className="text-sm font-medium mb-2 block">Endpoint URL</label>
          <div className="flex items-center gap-2">
            <code className="flex-1 bg-muted px-3 py-2 rounded text-sm">
              {apiEndpoint}
            </code>
            <Button
              variant="outline"
              size="sm"
              onClick={() => copyToClipboard(apiEndpoint, 'Endpoint URL')}
            >
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div>
          <label className="text-sm font-medium mb-2 block">Method & Headers</label>
          <div className="space-y-2">
            <Badge variant="outline">POST</Badge>
            <div className="text-xs space-y-1">
              <div><strong>Content-Type:</strong> application/json</div>
              <div className="flex items-center gap-2">
                <strong>x-api-key:</strong> 
                <span className="font-mono">
                  {showApiKey ? 'your-secret-api-key' : '••••••••••••••••'}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowApiKey(!showApiKey)}
                >
                  {showApiKey ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                </Button>
              </div>
            </div>
          </div>
        </div>

        <div>
          <label className="text-sm font-medium mb-2 block">Sample Payload</label>
          <div className="relative">
            <pre className="bg-muted p-3 rounded text-xs overflow-x-auto">
              {JSON.stringify(samplePayload, null, 2)}
            </pre>
            <Button
              variant="outline"
              size="sm"
              className="absolute top-2 right-2"
              onClick={() => copyToClipboard(JSON.stringify(samplePayload, null, 2), 'Sample payload')}
            >
              <Copy className="h-3 w-3" />
            </Button>
          </div>
        </div>

        <div>
          <label className="text-sm font-medium mb-2 block">cURL Example</label>
          <div className="relative">
            <pre className="bg-muted p-3 rounded text-xs overflow-x-auto">
              {curlExample}
            </pre>
            <Button
              variant="outline"
              size="sm"
              className="absolute top-2 right-2"
              onClick={() => copyToClipboard(curlExample, 'cURL example')}
            >
              <Copy className="h-3 w-3" />
            </Button>
          </div>
        </div>

        <div className="text-xs text-muted-foreground space-y-1">
          <p><strong>Required fields:</strong> timestamp, source, metrics</p>
          <p><strong>Optional fields:</strong> Any additional data will be stored in raw_data</p>
          <p><strong>Response:</strong> JSON with success status and data ID</p>
        </div>
      </CardContent>
    </Card>
  );
};

export default ApiEndpointInfo;
