import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, PieChart, Users, BarChart3, Maximize2, Minimize2 } from 'lucide-react';
import ChartRenderer from './ChartRenderer';

interface ChartGridProps {
  data: any;
  layoutMode: 'single' | 'quad';
  selectedChart: string;
  onChartSelect: (chartId: string) => void;
  onLayoutToggle: () => void;
}

const ChartGrid: React.FC<ChartGridProps> = ({
  data,
  layoutMode,
  selectedChart,
  onChartSelect,
  onLayoutToggle
}) => {
  const chartConfigs = {
    sales_performance: {
      title: 'Sales Performance',
      description: 'Monthly sales vs target comparison',
      icon: <TrendingUp className="h-4 w-4" />,
      type: 'line' as const,
      config: {
        xKey: 'month',
        yKey: ['sales', 'target'],
        colors: ['#B5792E', '#00BFFF'],
        referenceLines: [
          { value: 5000, stroke: '#22c55e', strokeDasharray: "5 5", label: "Goal" }
        ]
      }
    },
    market_share: {
      title: 'Market Share',
      description: 'Distribution across product lines',
      icon: <PieChart className="h-4 w-4" />,
      type: 'pie' as const,
      config: {
        colors: ['#B5792E', '#00BFFF', '#010100', '#22c55e', '#f59e0b']
      }
    },
    user_engagement: {
      title: 'User Engagement',
      description: 'Weekly active and new users',
      icon: <Users className="h-4 w-4" />,
      type: 'area' as const,
      config: {
        xKey: 'week',
        yKey: ['active_users', 'new_users'],
        colors: ['#B5792E', '#00BFFF']
      }
    },
    quarterly_performance: {
      title: 'Quarterly Performance',
      description: 'Revenue growth by quarter',
      icon: <BarChart3 className="h-4 w-4" />,
      type: 'bar' as const,
      config: {
        xKey: 'quarter',
        yKey: 'revenue',
        colors: ['#B5792E']
      }
    }
  };

  if (layoutMode === 'single') {
    const chart = chartConfigs[selectedChart as keyof typeof chartConfigs];
    const chartData = data?.[selectedChart];

    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {chart.icon}
              <CardTitle>{chart.title}</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="secondary">Single View</Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={onLayoutToggle}
              >
                <Minimize2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
          <CardDescription>{chart.description}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-96">
            {chartData && (
              <ChartRenderer
                type={chart.type}
                data={chartData}
                config={{ ...chart.config, height: 384 }}
              />
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Dashboard Overview</h3>
        <div className="flex items-center gap-2">
          <Badge variant="secondary">Grid View</Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={onLayoutToggle}
          >
            <Maximize2 className="h-4 w-4" />
          </Button>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Object.entries(chartConfigs).map(([chartId, chart]) => {
          const chartData = data?.[chartId];
          
          return (
            <Card 
              key={chartId}
              className="cursor-pointer hover:shadow-lg transition-all duration-200"
              onClick={() => onChartSelect(chartId)}
            >
              <CardHeader>
                <div className="flex items-center gap-2">
                  {chart.icon}
                  <CardTitle className="text-lg">{chart.title}</CardTitle>
                </div>
                <CardDescription>{chart.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  {chartData && (
                    <ChartRenderer
                      type={chart.type}
                      data={chartData}
                      config={{ ...chart.config, height: 256 }}
                    />
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};

export default ChartGrid;