import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import { Code, Database, Zap, ArrowRight, Copy, ExternalLink } from 'lucide-react';

const APIReference = () => {
  const endpoints = [
    {
      method: 'POST',
      path: '/upload',
      description: 'Upload dataset for processing',
      parameters: [
        { name: 'file', type: 'File', required: true, description: 'Dataset file (CSV, Excel, JSON)' },
        { name: 'name', type: 'String', required: false, description: 'Custom dataset name' }
      ],
      response: {
        dataset_id: 'string',
        filename: 'string',
        size: 'number',
        columns: 'array'
      }
    },
    {
      method: 'POST',
      path: '/clean',
      description: 'Run cleaning operations on uploaded dataset',
      parameters: [
        { name: 'file', type: 'File', required: true, description: 'Dataset file to clean' },
        { name: 'operations', type: 'Array', required: false, description: 'Specific cleaning operations' },
        { name: 'options', type: 'Object', required: false, description: 'Cleaning configuration' }
      ],
      response: {
        cleaned_data: 'object',
        operations_applied: 'array',
        summary: 'object'
      }
    },
    {
      method: 'POST',
      path: '/analyze/descriptive',
      description: 'Generate descriptive statistics and summaries',
      parameters: [
        { name: 'dataset_id', type: 'String', required: true, description: 'ID of uploaded dataset' },
        { name: 'columns', type: 'Array', required: false, description: 'Specific columns to analyze' }
      ],
      response: {
        statistics: 'object',
        visualizations: 'array',
        insights: 'array'
      }
    },
    {
      method: 'POST',
      path: '/analyze/diagnostic',
      description: 'Perform diagnostic analysis to understand data patterns',
      parameters: [
        { name: 'dataset_id', type: 'String', required: true, description: 'ID of uploaded dataset' },
        { name: 'target_column', type: 'String', required: true, description: 'Column to diagnose' }
      ],
      response: {
        correlations: 'object',
        patterns: 'array',
        anomalies: 'array'
      }
    },
    {
      method: 'POST',
      path: '/analyze/predictive',
      description: 'Run predictive models and forecasting',
      parameters: [
        { name: 'dataset_id', type: 'String', required: true, description: 'ID of uploaded dataset' },
        { name: 'target_column', type: 'String', required: true, description: 'Column to predict' },
        { name: 'model_type', type: 'String', required: false, description: 'Specific model to use' }
      ],
      response: {
        predictions: 'array',
        model_metrics: 'object',
        feature_importance: 'object'
      }
    },
    {
      method: 'POST',
      path: '/analyze/prescriptive',
      description: 'Generate prescriptive insights and recommendations',
      parameters: [
        { name: 'dataset_id', type: 'String', required: true, description: 'ID of uploaded dataset' },
        { name: 'objective', type: 'String', required: true, description: 'Business objective' }
      ],
      response: {
        recommendations: 'array',
        scenarios: 'object',
        action_plan: 'object'
      }
    },
    {
      method: 'POST',
      path: '/analyze/nlp',
      description: 'Natural language processing and text analysis',
      parameters: [
        { name: 'dataset_id', type: 'String', required: true, description: 'ID of uploaded dataset' },
        { name: 'text_column', type: 'String', required: true, description: 'Column containing text data' },
        { name: 'analysis_type', type: 'String', required: false, description: 'Type of NLP analysis' }
      ],
      response: {
        sentiment: 'object',
        topics: 'array',
        entities: 'array'
      }
    },
    {
      method: 'GET',
      path: '/export/{dataset_id}',
      description: 'Export processed data and results',
      parameters: [
        { name: 'dataset_id', type: 'String', required: true, description: 'ID of dataset to export' },
        { name: 'format', type: 'String', required: false, description: 'Export format (csv, excel, json)' }
      ],
      response: {
        download_url: 'string',
        expires_at: 'string'
      }
    },
    {
      method: 'GET',
      path: '/dashboard/{dataset_id}',
      description: 'Access dashboard data and visualizations',
      parameters: [
        { name: 'dataset_id', type: 'String', required: true, description: 'ID of dataset' }
      ],
      response: {
        dashboard_url: 'string',
        widgets: 'array',
        last_updated: 'string'
      }
    }
  ];

  const getMethodColor = (method: string) => {
    switch (method) {
      case 'GET': return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
      case 'POST': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400';
      case 'PUT': return 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400';
      case 'DELETE': return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
    }
  };

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <main className="flex-grow">
        {/* Hero Section */}
        <section className="py-16 bg-gradient-to-br from-savvy-dark via-savvy-midnight to-savvy-slate text-white">
          <div className="container px-4 md:px-6">
            <div className="text-center max-w-4xl mx-auto">
              <Code className="h-16 w-16 text-savvy-gold mx-auto mb-6" />
              <h1 className="text-4xl md:text-5xl font-bold mb-6">
                API
                <span className="text-savvy-gold"> Reference</span>
              </h1>
              <p className="text-xl text-gray-300 max-w-2xl mx-auto mb-8">
                Complete reference for all SAINT API endpoints, parameters, and responses.
              </p>
              <Badge className="bg-savvy-gold/20 text-savvy-gold border-savvy-gold/30">
                Private Beta - Coming Soon
              </Badge>
            </div>
          </div>
        </section>

        {/* Quick Info */}
        <section className="py-12 bg-white dark:bg-savvy-dark border-b">
          <div className="container px-4 md:px-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              <Card className="text-center">
                <CardContent className="p-6">
                  <Database className="h-8 w-8 text-savvy-blue mx-auto mb-3" />
                  <h3 className="font-semibold mb-2">Base URL</h3>
                  <code className="text-sm bg-muted px-2 py-1 rounded">
                    https://api.savvyclean.com/v1
                  </code>
                </CardContent>
              </Card>
              
              <Card className="text-center">
                <CardContent className="p-6">
                  <Zap className="h-8 w-8 text-savvy-gold mx-auto mb-3" />
                  <h3 className="font-semibold mb-2">Authentication</h3>
                  <code className="text-sm bg-muted px-2 py-1 rounded">
                    Bearer Token
                  </code>
                </CardContent>
              </Card>
              
              <Card className="text-center">
                <CardContent className="p-6">
                  <Code className="h-8 w-8 text-savvy-blue mx-auto mb-3" />
                  <h3 className="font-semibold mb-2">Content-Type</h3>
                  <code className="text-sm bg-muted px-2 py-1 rounded">
                    application/json
                  </code>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* Endpoints */}
        <section className="py-16 bg-gradient-to-r from-savvy-blue/5 to-savvy-gold/5">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">API Endpoints</h2>
              <p className="text-muted-foreground">
                Comprehensive list of available endpoints and their specifications.
              </p>
            </div>
            
            <div className="space-y-6 max-w-6xl mx-auto">
              {endpoints.map((endpoint, index) => (
                <Card key={index} className="shadow-sm hover:shadow-lg transition-all duration-300">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <Badge className={getMethodColor(endpoint.method)}>
                          {endpoint.method}
                        </Badge>
                        <code className="text-lg font-mono">{endpoint.path}</code>
                      </div>
                      <Button size="sm" variant="ghost">
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                    <p className="text-muted-foreground mt-2">{endpoint.description}</p>
                  </CardHeader>
                  
                  <CardContent>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* Parameters */}
                      <div>
                        <h4 className="font-semibold mb-3 flex items-center gap-2">
                          <ArrowRight className="h-4 w-4 text-savvy-blue" />
                          Parameters
                        </h4>
                        <div className="space-y-3">
                          {endpoint.parameters.map((param, paramIndex) => (
                            <div key={paramIndex} className="border rounded-lg p-3 bg-card/50">
                              <div className="flex items-center gap-2 mb-1">
                                <code className="text-sm font-mono">{param.name}</code>
                                <Badge variant="outline" className="text-xs">
                                  {param.type}
                                </Badge>
                                {param.required && (
                                  <Badge variant="destructive" className="text-xs">
                                    Required
                                  </Badge>
                                )}
                              </div>
                              <p className="text-xs text-muted-foreground">{param.description}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      {/* Response */}
                      <div>
                        <h4 className="font-semibold mb-3 flex items-center gap-2">
                          <ArrowRight className="h-4 w-4 text-savvy-gold" />
                          Response
                        </h4>
                        <div className="border rounded-lg p-4 bg-card/50">
                          <pre className="text-sm overflow-x-auto">
                            <code className="text-muted-foreground">
                              {JSON.stringify(endpoint.response, null, 2)}
                            </code>
                          </pre>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* SDK and Libraries */}
        <section className="py-16 bg-white dark:bg-savvy-dark">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">SDKs & Libraries</h2>
              <p className="text-muted-foreground">
                Official SDKs and community libraries for popular programming languages.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              {[
                { name: 'Python SDK', status: 'Coming Soon', icon: '🐍' },
                { name: 'JavaScript SDK', status: 'Coming Soon', icon: '🟨' },
                { name: 'R Package', status: 'Planned', icon: '📊' }
              ].map((sdk, index) => (
                <Card key={index} className="text-center shadow-sm border-dashed">
                  <CardContent className="p-6">
                    <div className="text-4xl mb-4">{sdk.icon}</div>
                    <h3 className="font-semibold mb-2">{sdk.name}</h3>
                    <Badge variant="secondary">{sdk.status}</Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-16 bg-gradient-to-br from-savvy-dark via-savvy-midnight to-savvy-slate text-white">
          <div className="container px-4 md:px-6">
            <div className="text-center max-w-3xl mx-auto">
              <h2 className="text-3xl font-bold mb-4">Ready to Integrate?</h2>
              <p className="text-gray-300 mb-8">
                Join our private beta program and get early access to the SAINT API.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button className="bg-savvy-gold text-savvy-dark hover:bg-savvy-gold/90">
                  Request Beta Access
                </Button>
                <Button variant="outline" className="border-white text-white hover:bg-white/10">
                  <ExternalLink className="h-4 w-4 mr-2" />
                  View Examples
                </Button>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default APIReference;