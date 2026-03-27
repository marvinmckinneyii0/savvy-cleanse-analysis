import React from 'react';
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';

interface ChartData {
  [key: string]: any;
}

interface ChartRendererProps {
  type: 'line' | 'area' | 'bar' | 'pie';
  data: ChartData[];
  config: {
    xKey?: string;
    yKey?: string | string[];
    colors?: string[];
    showGrid?: boolean;
    showLegend?: boolean;
    showTooltip?: boolean;
    height?: number;
    referenceLines?: Array<{
      value: number;
      stroke?: string;
      strokeDasharray?: string;
      label?: string;
    }>;
  };
  className?: string;
}

const ChartRenderer: React.FC<ChartRendererProps> = ({ 
  type, 
  data, 
  config, 
  className = "" 
}) => {
  const {
    xKey = 'x',
    yKey = 'y',
    colors = ['#B5792E', '#00BFFF', '#010100', '#22c55e', '#f59e0b'],
    showGrid = true,
    showLegend = true,
    showTooltip = true,
    height = 300,
    referenceLines = []
  } = config;

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-background border border-border rounded-lg p-3 shadow-lg">
          <p className="font-medium text-sm">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }} className="text-sm">
              {entry.name}: {typeof entry.value === 'number' ? entry.value.toLocaleString() : entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const renderChart = () => {
    const commonProps = {
      data,
      margin: { top: 5, right: 30, left: 20, bottom: 5 }
    };

    switch (type) {
      case 'line':
        return (
          <LineChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />}
            <XAxis dataKey={xKey} stroke="hsl(var(--muted-foreground))" />
            <YAxis stroke="hsl(var(--muted-foreground))" />
            {showTooltip && <Tooltip content={<CustomTooltip />} />}
            {showLegend && <Legend />}
            {referenceLines.map((refLine, index) => (
              <ReferenceLine 
                key={index}
                y={refLine.value}
                stroke={refLine.stroke || colors[1]}
                strokeDasharray={refLine.strokeDasharray || "5 5"}
                label={refLine.label}
              />
            ))}
            {Array.isArray(yKey) ? (
              yKey.map((key, index) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={colors[index % colors.length]}
                  strokeWidth={3}
                  dot={{ fill: colors[index % colors.length], strokeWidth: 2, r: 6 }}
                  activeDot={{ r: 8, stroke: colors[index % colors.length], strokeWidth: 2 }}
                  name={key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                />
              ))
            ) : (
              <Line
                type="monotone"
                dataKey={yKey}
                stroke={colors[0]}
                strokeWidth={3}
                dot={{ fill: colors[0], strokeWidth: 2, r: 6 }}
                activeDot={{ r: 8, stroke: colors[0], strokeWidth: 2 }}
              />
            )}
          </LineChart>
        );

      case 'area':
        return (
          <AreaChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />}
            <XAxis dataKey={xKey} stroke="hsl(var(--muted-foreground))" />
            <YAxis stroke="hsl(var(--muted-foreground))" />
            {showTooltip && <Tooltip content={<CustomTooltip />} />}
            {showLegend && <Legend />}
            {Array.isArray(yKey) ? (
              yKey.map((key, index) => (
                <Area
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stackId="1"
                  stroke={colors[index % colors.length]}
                  fill={colors[index % colors.length]}
                  fillOpacity={0.6}
                  name={key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                />
              ))
            ) : (
              <Area
                type="monotone"
                dataKey={yKey}
                stroke={colors[0]}
                fill={colors[0]}
                fillOpacity={0.6}
              />
            )}
          </AreaChart>
        );

      case 'bar':
        return (
          <BarChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />}
            <XAxis dataKey={xKey} stroke="hsl(var(--muted-foreground))" />
            <YAxis stroke="hsl(var(--muted-foreground))" />
            {showTooltip && <Tooltip content={<CustomTooltip />} />}
            {showLegend && <Legend />}
            {Array.isArray(yKey) ? (
              yKey.map((key, index) => (
                <Bar
                  key={key}
                  dataKey={key}
                  fill={colors[index % colors.length]}
                  radius={[4, 4, 0, 0]}
                  name={key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                />
              ))
            ) : (
              <Bar
                dataKey={yKey}
                fill={colors[0]}
                radius={[4, 4, 0, 0]}
              />
            )}
          </BarChart>
        );

      case 'pie':
        return (
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, value, percent }: any) => `${name}: ${percent ? Math.round(percent * 100) : Math.round((value / data.reduce((sum: number, item: any) => sum + item.value, 0)) * 100)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
              ))}
            </Pie>
            {showTooltip && <Tooltip content={<CustomTooltip />} />}
            {showLegend && <Legend />}
          </PieChart>
        );

      default:
        return <div>Unsupported chart type</div>;
    }
  };

  return (
    <div className={`w-full ${className}`}>
      <ResponsiveContainer width="100%" height={height}>
        {renderChart()}
      </ResponsiveContainer>
    </div>
  );
};

export default ChartRenderer;