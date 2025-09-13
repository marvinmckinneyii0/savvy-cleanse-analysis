import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Upload, 
  BarChart3, 
  Brain, 
  MessageSquare, 
  FileText, 
  TrendingUp, 
  Calendar,
  Database,
  Activity,
  Sparkles
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface Dataset {
  id: string;
  filename: string;
  original_filename: string;
  status: string;
  created_at: string;
  metadata: {
    rows: number;
    columns: number;
    column_names: string[];
  };
}

interface AnalysisResult {
  id: string;
  analysis_type: string;
  created_at: string;
  results: any;
}

interface NLPQuery {
  id: string;
  query_text: string;
  analysis_type: string;
  created_at: string;
  results: any;
}

interface DashboardStats {
  total_datasets: number;
  total_analyses: number;
  total_nlp_queries: number;
}

const UserDashboard: React.FC = () => {
  // Mock user data since auth is removed
  const user = { id: '00000000-0000-4000-8000-000000000001', email: 'user@example.com' };
  const session = { access_token: 'mock-token' };
  const { toast } = useToast();
  
  // State management
  const [dashboardData, setDashboardData] = useState<{
    user_stats: DashboardStats;
    recent_datasets: Dataset[];
    recent_analyses: AnalysisResult[];
    recent_queries: NLPQuery[];
  } | null>(null);
  
  const [selectedDataset, setSelectedDataset] = useState<string>('');
  const [nlpQuery, setNlpQuery] = useState<string>('');
  const [llmProvider, setLlmProvider] = useState<string>('openai');
  const [loading, setLoading] = useState(false);
  const [nlpResult, setNlpResult] = useState<any>(null);

  // Fetch dashboard data
  useEffect(() => {
    // Always fetch data since we're using mock data
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // For now, use mock data since auth is disabled
      const mockData = {
        user_stats: {
          total_datasets: 3,
          total_analyses: 7,
          total_nlp_queries: 2
        },
        recent_datasets: [
          {
            id: "1",
            filename: "sales_data.csv",
            original_filename: "sales_data.csv",
            status: "cleaned",
            created_at: new Date().toISOString(),
            metadata: {
              rows: 1000,
              columns: 8,
              column_names: ["date", "sales", "region", "product"]
            }
          },
          {
            id: "2", 
            filename: "customer_data.xlsx",
            original_filename: "customer_data.xlsx",
            status: "uploaded",
            created_at: new Date(Date.now() - 86400000).toISOString(),
            metadata: {
              rows: 500,
              columns: 12,
              column_names: ["id", "name", "email", "age", "location"]
            }
          }
        ],
        recent_analyses: [
          {
            id: "1",
            analysis_type: "descriptive",
            created_at: new Date().toISOString(),
            results: {}
          },
          {
            id: "2",
            analysis_type: "predictive", 
            created_at: new Date(Date.now() - 3600000).toISOString(),
            results: {}
          }
        ],
        recent_queries: [
          {
            id: "1",
            query_text: "What factors most influence sales performance?",
            analysis_type: "diagnostic",
            created_at: new Date().toISOString(),
            results: {}
          }
        ]
      };
      
      setDashboardData(mockData);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load dashboard data',
        variant: 'destructive',
      });
    }
  };

  const handleNLPQuery = async () => {
    if (!nlpQuery.trim() || !selectedDataset) {
      toast({
        title: 'Error',
        description: 'Please select a dataset and enter a query',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`/analyze/nlp/${selectedDataset}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.access_token}`,
        },
        body: JSON.stringify({
          query: nlpQuery,
          llm_provider: llmProvider,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setNlpResult(result);
        toast({
          title: 'Success',
          description: 'Query processed successfully',
        });
        
        // Refresh dashboard data
        fetchDashboardData();
      } else {
        throw new Error('Failed to process query');
      }
    } catch (error) {
      console.error('Error processing NLP query:', error);
      toast({
        title: 'Error',
        description: 'Failed to process your query',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'uploaded': return 'bg-blue-500';
      case 'cleaned': return 'bg-green-500';
      case 'analyzed': return 'bg-purple-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!dashboardData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Activity className="mx-auto h-8 w-8 animate-spin text-muted-foreground" />
          <p className="mt-2 text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Welcome back!</h1>
          <p className="text-muted-foreground">
            Here's what's happening with your data analytics.
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Datasets</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.user_stats.total_datasets}</div>
            <p className="text-xs text-muted-foreground">
              Data files uploaded and processed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Analyses Performed</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.user_stats.total_analyses}</div>
            <p className="text-xs text-muted-foreground">
              Statistical and ML analyses completed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">NLP Queries</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.user_stats.total_nlp_queries}</div>
            <p className="text-xs text-muted-foreground">
              Natural language questions asked
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Natural Language Query Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            Ask Questions About Your Data
          </CardTitle>
          <CardDescription>
            Use natural language to analyze your datasets. Ask questions like "What's the correlation between sales and marketing spend?"
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Select Dataset</label>
              <select
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={selectedDataset}
                onChange={(e) => setSelectedDataset(e.target.value)}
              >
                <option value="">Choose a dataset...</option>
                {dashboardData.recent_datasets.map((dataset) => (
                  <option key={dataset.id} value={dataset.id}>
                    {dataset.original_filename} ({dataset.metadata.rows} rows)
                  </option>
                ))}
              </select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">AI Model</label>
              <select
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={llmProvider}
                onChange={(e) => setLlmProvider(e.target.value)}
              >
                <option value="openai">OpenAI GPT-4</option>
                <option value="anthropic">Anthropic Claude</option>
                <option value="gemini">Google Gemini</option>
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Your Question</label>
            <Textarea
              placeholder="e.g., What factors most influence customer satisfaction? Which features predict sales best? How can I optimize my marketing spend?"
              value={nlpQuery}
              onChange={(e) => setNlpQuery(e.target.value)}
              className="min-h-[80px]"
            />
          </div>

          <Button 
            onClick={handleNLPQuery} 
            disabled={loading || !selectedDataset || !nlpQuery.trim()}
            className="w-full"
          >
            {loading ? (
              <>
                <Activity className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <MessageSquare className="mr-2 h-4 w-4" />
                Ask Question
              </>
            )}
          </Button>

          {nlpResult && (
            <Alert>
              <Sparkles className="h-4 w-4" />
              <AlertDescription>
                <div className="space-y-2">
                  <p className="font-medium">Analysis Result:</p>
                  <p>{nlpResult.natural_language_response || 'Analysis completed successfully. Check detailed results below.'}</p>
                  {nlpResult.intent && (
                    <div className="text-xs text-muted-foreground">
                      Analysis Type: {nlpResult.intent.analysis_type} | Confidence: {(nlpResult.intent.confidence * 100).toFixed(1)}%
                    </div>
                  )}
                </div>
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Recent Datasets */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Recent Datasets
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {dashboardData.recent_datasets.length === 0 ? (
                <p className="text-sm text-muted-foreground">No datasets uploaded yet.</p>
              ) : (
                dashboardData.recent_datasets.map((dataset) => (
                  <div key={dataset.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="space-y-1">
                      <p className="font-medium text-sm">{dataset.original_filename}</p>
                      <p className="text-xs text-muted-foreground">
                        {dataset.metadata.rows} rows × {dataset.metadata.columns} columns
                      </p>
                      <p className="text-xs text-muted-foreground">
                        <Calendar className="inline h-3 w-3 mr-1" />
                        {formatDate(dataset.created_at)}
                      </p>
                    </div>
                    <Badge className={`${getStatusColor(dataset.status)} text-white`}>
                      {dataset.status}
                    </Badge>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Recent Analyses */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Recent Analyses
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {dashboardData.recent_analyses.length === 0 ? (
                <p className="text-sm text-muted-foreground">No analyses performed yet.</p>
              ) : (
                dashboardData.recent_analyses.map((analysis) => (
                  <div key={analysis.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="space-y-1">
                      <p className="font-medium text-sm capitalize">{analysis.analysis_type} Analysis</p>
                      <p className="text-xs text-muted-foreground">
                        <Calendar className="inline h-3 w-3 mr-1" />
                        {formatDate(analysis.created_at)}
                      </p>
                    </div>
                    <Badge variant="outline">
                      {analysis.analysis_type}
                    </Badge>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent NLP Queries */}
      {dashboardData.recent_queries.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              Recent Questions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {dashboardData.recent_queries.map((query) => (
                <div key={query.id} className="p-3 border rounded-lg">
                  <p className="font-medium text-sm mb-1">"{query.query_text}"</p>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>Analysis: {query.analysis_type || 'General'}</span>
                    <span>{formatDate(query.created_at)}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default UserDashboard;