/**
 * Dashboard API utilities for fetching chart data and analytics
 */

export interface DashboardData {
  sales_performance: Array<{
    month: string;
    sales: number;
    target: number;
  }>;
  market_share: Array<{
    name: string;
    value: number;
    percentage: number;
  }>;
  user_engagement: Array<{
    week: string;
    active_users: number;
    new_users: number;
  }>;
  quarterly_performance: Array<{
    quarter: string;
    revenue: number;
    growth: number;
  }>;
  metadata?: {
    generated_at: string;
    analysis_mode: string;
    filters_applied: Record<string, string>;
    data_quality_score: number;
    last_updated: string;
  };
  insights?: any;
  forecasts?: any;
  recommendations?: any;
}

export interface DashboardFilterOptions {
  analysis_mode?: string;
  date_range?: string;
  region?: string;
  category?: string;
}

const generateMockData = (filters: DashboardFilterOptions = {}): DashboardData => {
  const mode = filters.analysis_mode || 'descriptive';
  
  return {
    sales_performance: [
      { month: 'Jan', sales: 4200, target: 4000 },
      { month: 'Feb', sales: 3800, target: 4100 },
      { month: 'Mar', sales: 5100, target: 4200 },
      { month: 'Apr', sales: 4600, target: 4300 },
      { month: 'May', sales: 5400, target: 4400 },
      { month: 'Jun', sales: 4900, target: 4500 }
    ],
    market_share: [
      { name: 'Product A', value: 4500, percentage: 35 },
      { name: 'Product B', value: 3200, percentage: 25 },
      { name: 'Product C', value: 2600, percentage: 20 },
      { name: 'Product D', value: 1900, percentage: 15 },
      { name: 'Others', value: 650, percentage: 5 }
    ],
    user_engagement: [
      { week: 'Week 1', active_users: 1200, new_users: 180 },
      { week: 'Week 2', active_users: 1350, new_users: 220 },
      { week: 'Week 3', active_users: 1180, new_users: 160 },
      { week: 'Week 4', active_users: 1420, new_users: 280 }
    ],
    quarterly_performance: [
      { quarter: 'Q1 2023', revenue: 125000, growth: 12 },
      { quarter: 'Q2 2023', revenue: 142000, growth: 18 },
      { quarter: 'Q3 2023', revenue: 158000, growth: 22 },
      { quarter: 'Q4 2023', revenue: 175000, growth: 28 }
    ],
    metadata: {
      generated_at: new Date().toISOString(),
      analysis_mode: mode,
      filters_applied: filters as Record<string, string>,
      data_quality_score: 8.9,
      last_updated: new Date().toISOString()
    }
  };
};

export const fetchDashboardData = async (filters: DashboardFilterOptions = {}): Promise<DashboardData> => {
  // Return local mock data (no backend server available)
  return generateMockData(filters);
};

export const runDashboardAnalysis = async (
  analysisType: string,
  _datasetId?: string,
  _targetColumn?: string,
  _filters?: Record<string, any>
): Promise<any> => {
  // Mock response since no backend is available
  return {
    analysis_type: analysisType,
    status: 'completed',
    results: {
      summary: `${analysisType} analysis completed successfully`,
      metrics: { accuracy: 0.92, confidence: 0.87 }
    }
  };
};

export const exportDashboardData = async (
  format: string = 'json',
  _charts?: string[]
): Promise<any> => {
  // Mock export
  return {
    status: 'success',
    format,
    download_url: '#',
    message: 'Export generated successfully'
  };
};

export const getDashboardSummary = async (): Promise<any> => {
  return {
    total_datasets: 15,
    total_analyses: 47,
    active_dashboards: 8,
    data_quality_avg: 8.9,
    system_status: 'healthy'
  };
};