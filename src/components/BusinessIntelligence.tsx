
import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegend, ChartLegendContent } from '@/components/ui/chart';
import { AreaChart, BarChart, LineChart, PieChart, Area, Bar, Line, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Sample data for charts
const salesData = [
  { month: 'Jan', sales: 4000, target: 2400 },
  { month: 'Feb', sales: 3000, target: 2500 },
  { month: 'Mar', sales: 5000, target: 2600 },
  { month: 'Apr', sales: 2780, target: 2700 },
  { month: 'May', sales: 1890, target: 2800 },
  { month: 'Jun', sales: 2390, target: 2900 },
  { month: 'Jul', sales: 3490, target: 3000 },
];

const marketShareData = [
  { name: 'Product A', value: 400 },
  { name: 'Product B', value: 300 },
  { name: 'Product C', value: 300 },
  { name: 'Product D', value: 200 },
];

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

const userEngagementData = [
  { name: 'Week 1', newUsers: 400, activeUsers: 240 },
  { name: 'Week 2', newUsers: 300, activeUsers: 398 },
  { name: 'Week 3', newUsers: 200, activeUsers: 423 },
  { name: 'Week 4', newUsers: 278, activeUsers: 450 },
];

const performanceData = [
  { name: 'Q1', value: 2400 },
  { name: 'Q2', value: 1398 },
  { name: 'Q3', value: 9800 },
  { name: 'Q4', value: 3908 },
];

const BusinessIntelligence = () => {
  return (
    <section className="py-16 bg-background" id="business-intelligence">
      <div className="container px-4 md:px-6">
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold mb-2">Business Intelligence</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Transform your data into actionable insights with our powerful analytics visualization tools.
          </p>
        </div>
        
        <div className="grid gap-6 md:grid-cols-2">
          {/* Sales Performance Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Sales Performance</CardTitle>
              <CardDescription>Monthly sales vs target comparison</CardDescription>
            </CardHeader>
            <CardContent className="h-80">
              <ChartContainer
                config={{
                  sales: { label: "Sales", color: "#B5792E" },
                  target: { label: "Target", color: "#010100" },
                }}
              >
                <LineChart
                  data={salesData}
                  margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Line type="monotone" dataKey="sales" name="sales" stroke="var(--color-sales, #B5792E)" activeDot={{ r: 8 }} />
                  <Line type="monotone" dataKey="target" name="target" stroke="var(--color-target, #010100)" strokeDasharray="5 5" />
                  <ChartLegend content={<ChartLegendContent />} />
                </LineChart>
              </ChartContainer>
            </CardContent>
          </Card>
          
          {/* Market Share Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Market Share</CardTitle>
              <CardDescription>Distribution across product lines</CardDescription>
            </CardHeader>
            <CardContent className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={marketShareData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {marketShareData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
          
          {/* User Engagement Chart */}
          <Card>
            <CardHeader>
              <CardTitle>User Engagement</CardTitle>
              <CardDescription>Weekly new and active users</CardDescription>
            </CardHeader>
            <CardContent className="h-80">
              <ChartContainer
                config={{
                  newUsers: { label: "New Users", color: "#B5792E" },
                  activeUsers: { label: "Active Users", color: "#00BFFF" },
                }}
              >
                <AreaChart
                  data={userEngagementData}
                  margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Area type="monotone" dataKey="activeUsers" name="activeUsers" stackId="1" stroke="var(--color-activeUsers, #00BFFF)" fill="var(--color-activeUsers, #00BFFF)" fillOpacity={0.5} />
                  <Area type="monotone" dataKey="newUsers" name="newUsers" stackId="1" stroke="var(--color-newUsers, #B5792E)" fill="var(--color-newUsers, #B5792E)" fillOpacity={0.5} />
                  <ChartLegend content={<ChartLegendContent />} />
                </AreaChart>
              </ChartContainer>
            </CardContent>
          </Card>
          
          {/* Performance Metrics Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Quarterly Performance</CardTitle>
              <CardDescription>Financial metrics by quarter</CardDescription>
            </CardHeader>
            <CardContent className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={performanceData}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="value" name="Revenue" fill="#B5792E" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default BusinessIntelligence;
