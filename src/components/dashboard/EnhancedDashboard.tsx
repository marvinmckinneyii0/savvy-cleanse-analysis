import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  BarChart3, 
  TrendingUp, 
  PieChart, 
  Activity, 
  Filter,
  Download,
  RefreshCw,
  Calendar,
  Users,
  DollarSign
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  PieChart as RechartsPieChart, 
  Cell, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { useToast } from '@/hooks/use-toast';
import { fetchDashboardData, DashboardData, DashboardFilters } from '@/utils/dashboardApi';
import ChartGrid from './ChartGrid';

interface FilterState extends DashboardFilters {
  customFilter: string;
}

type AnalysisMode = 'descriptive' | 'diagnostic' | 'predictive' | 'prescriptive';

const EnhancedDashboard: React.FC = () => {
  const { toast } = useToast();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(false);
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>('descriptive');
  const [layoutMode, setLayoutMode] = useState<'single' | 'quad'>('quad');
  const [selectedChart, setSelectedChart] = useState<string>('sales_performance');
  const [filters, setFilters] = useState<FilterState>({
    dateRange: 'last_30_days',
    region: 'all',
    category: 'all',
    customFilter: ''
  });

  // Chart colors matching the dark theme
  const chartColors = {
    primary: '#B5792E', // Gold
    secondary: '#00BFFF', // Blue
    tertiary: '#010100', // Black
    success: '#22c55e',
    warning: '#f59e0b',
    error: '#ef4444'
  };

  const pieColors = ['#B5792E', '#00BFFF', '#010100', '#22c55e', '#f59e0b'];

  useEffect(() => {
    loadDashboardData();
  }, [analysisMode, filters]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const data = await fetchDashboardData({
        analysis_mode: analysisMode,
        date_range: filters.dateRange,
        region: filters.region,
        category: filters.category
      });
      setDashboardData(data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load dashboard data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAnalysisModeChange = (mode: AnalysisMode) => {
    setAnalysisMode(mode);
    toast({
      title: 'Analysis Mode Changed',
      description: `Switched to ${mode} analytics mode`,
    });
  };

  const handleFilterChange = (key: keyof FilterState, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleApplyFilters = () => {
    loadDashboardData();
  };

  const handleResetFilters = () => {
    setFilters({
      dateRange: 'last_30_days',
      region: 'all',
      category: 'all',
      customFilter: ''
    });
  };

  const exportData = () => {
    toast({
      title: 'Export Started',
      description: 'Dashboard data is being prepared for download',
    });
  };

  const analysisButtons = [
    { id: 'descriptive', label: 'Descriptive', description: 'What happened?' },
    { id: 'diagnostic', label: 'Diagnostic', description: 'Why did it happen?' },
    { id: 'predictive', label: 'Predictive', description: 'What will happen?' },
    { id: 'prescriptive', label: 'Prescriptive', description: 'What should we do?' }
  ];

  const summaryStats = dashboardData ? [
    {
      title: 'Total Revenue',
      value: '$2.1M',
      change: '+12.5%',
      icon: <DollarSign className="h-4 w-4" />,
      trend: 'up'
    },
    {
      title: 'Active Users',
      value: '1,620',
      change: '+8.2%',
      icon: <Users className="h-4 w-4" />,
      trend: 'up'
    },
    {
      title: 'Conversion Rate',
      value: '3.24%',
      change: '-0.1%',
      icon: <TrendingUp className="h-4 w-4" />,
      trend: 'down'
    },
    {
      title: 'Avg. Order Value',
      value: '$127',
      change: '+5.7%',
      icon: <BarChart3 className="h-4 w-4" />,
      trend: 'up'
    }
  ] : [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Activity className="mx-auto h-8 w-8 animate-spin text-muted-foreground" />
          <p className="mt-2 text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Analysis Mode Buttons */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Analytics Dashboard
              </CardTitle>
              <CardDescription>
                Choose your analysis mode and explore your data insights
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setLayoutMode(layoutMode === 'single' ? 'quad' : 'single')}
              >
                {layoutMode === 'single' ? 'Grid View' : 'Single View'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={loadDashboardData}
                disabled={loading}
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={exportData}
              >
                <Download className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {analysisButtons.map((button) => (
              <Button
                key={button.id}
                variant={analysisMode === button.id ? "default" : "outline"}
                className={`h-auto p-4 flex flex-col items-center gap-2 ${
                  analysisMode === button.id 
                    ? 'bg-savvy-gold text-savvy-dark hover:bg-savvy-gold/90' 
                    : 'hover:bg-muted'
                }`}
                onClick={() => handleAnalysisModeChange(button.id as AnalysisMode)}
              >
                <span className="font-medium">{button.label}</span>
                <span className="text-xs opacity-80">{button.description}</span>
              </Button>
            ))}
          </div>
          
          <Badge variant="secondary" className="mt-4">
            Current Mode: {analysisMode.charAt(0).toUpperCase() + analysisMode.slice(1)}
          </Badge>
        </CardContent>
      </Card>

      {/* Chart Grid */}
      <ChartGrid
        data={dashboardData}
        layoutMode={layoutMode}
        selectedChart={selectedChart}
        onChartSelect={setSelectedChart}
        onLayoutToggle={() => setLayoutMode(layoutMode === 'single' ? 'quad' : 'single')}
      />

      {/* Summary Statistics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Key Metrics Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {summaryStats.map((stat, index) => (
              <div key={index} className="p-4 border rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  {stat.icon}
                  <span className="text-sm font-medium">{stat.title}</span>
                </div>
                <div className="text-2xl font-bold">{stat.value}</div>
                <div className={`text-sm ${
                  stat.trend === 'up' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {stat.change}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <DashboardFilters
        filters={filters}
        onFilterChange={handleFilterChange}
        onApplyFilters={handleApplyFilters}
        onResetFilters={handleResetFilters}
        loading={loading}
      />

      {/* Analysis Results */}
      {analysisMode !== 'descriptive' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              {analysisMode.charAt(0).toUpperCase() + analysisMode.slice(1)} Analysis Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Alert>
              <AlertDescription>
                {analysisMode === 'diagnostic' && 
                  "Correlation analysis shows strong positive relationship between marketing spend and sales (r=0.78, p<0.001). Regional performance varies significantly with North America leading by 23%."}
                {analysisMode === 'predictive' && 
                  "Forecast models predict 15% revenue growth next quarter based on current trends. Confidence interval: 12-18%. Key drivers: user engagement (+0.3) and market expansion (+0.2)."}
                {analysisMode === 'prescriptive' && 
                  "Optimization recommendations: Increase marketing spend in Q2 by 20% for maximum ROI. Focus on Product A expansion in Europe. Expected outcome: +$340K revenue."}
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default EnhancedDashboard;