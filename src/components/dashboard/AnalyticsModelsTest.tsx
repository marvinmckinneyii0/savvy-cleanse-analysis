
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { runAllAnalytics } from '@/utils/analyticsModels';
import { 
  AreaChart, BarChart, LineChart, ScatterChart, 
  Area, Bar, Line, Scatter, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer 
} from 'recharts';

const AnalyticsModelsTest = () => {
  const [analyticsResults, setAnalyticsResults] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const runAnalytics = () => {
    setLoading(true);
    // Simulate API delay
    setTimeout(() => {
      const results = runAllAnalytics();
      setAnalyticsResults(results);
      setLoading(false);
    }, 500);
  };

  // Format numbers for display
  const formatNumber = (num: number) => {
    return parseFloat(num.toFixed(2)).toString();
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Analytics Models Test</CardTitle>
          <CardDescription>
            Test the functionality of descriptive, diagnostic, predictive, and prescriptive models
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button 
            onClick={runAnalytics} 
            disabled={loading}
            className="bg-savvy-gold hover:bg-savvy-gold/80 text-white"
          >
            {loading ? 'Processing...' : 'Run Analytics Models'}
          </Button>
          
          {analyticsResults && (
            <Tabs defaultValue="descriptive" className="mt-6">
              <TabsList className="grid grid-cols-4 mb-4">
                <TabsTrigger value="descriptive">Descriptive</TabsTrigger>
                <TabsTrigger value="diagnostic">Diagnostic</TabsTrigger>
                <TabsTrigger value="predictive">Predictive</TabsTrigger>
                <TabsTrigger value="prescriptive">Prescriptive</TabsTrigger>
              </TabsList>
              
              {/* Descriptive Analytics Tab */}
              <TabsContent value="descriptive">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Summary Statistics</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="stat-card">
                          <p className="text-sm text-muted-foreground">Mean</p>
                          <p className="text-2xl font-semibold">
                            {formatNumber(analyticsResults.descriptive.summaryStats.mean)}
                          </p>
                        </div>
                        <div className="stat-card">
                          <p className="text-sm text-muted-foreground">Median</p>
                          <p className="text-2xl font-semibold">
                            {formatNumber(analyticsResults.descriptive.summaryStats.median)}
                          </p>
                        </div>
                        <div className="stat-card">
                          <p className="text-sm text-muted-foreground">Mode</p>
                          <p className="text-2xl font-semibold">
                            {formatNumber(analyticsResults.descriptive.summaryStats.mode)}
                          </p>
                        </div>
                        <div className="stat-card">
                          <p className="text-sm text-muted-foreground">Std. Deviation</p>
                          <p className="text-2xl font-semibold">
                            {formatNumber(analyticsResults.descriptive.summaryStats.stdDev)}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardHeader>
                      <CardTitle>Frequency Distribution</CardTitle>
                    </CardHeader>
                    <CardContent className="h-60">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={analyticsResults.descriptive.frequencyDistribution}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis 
                            dataKey="binStart" 
                            tickFormatter={(value) => formatNumber(value)} 
                          />
                          <YAxis />
                          <Tooltip formatter={(value) => [value, 'Count']} />
                          <Bar dataKey="count" fill="#B5792E" name="Frequency" />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                  
                  <Card className="lg:col-span-2">
                    <CardHeader>
                      <CardTitle>Data Points</CardTitle>
                    </CardHeader>
                    <CardContent className="h-60">
                      <ResponsiveContainer width="100%" height="100%">
                        <ScatterChart>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis 
                            type="number" 
                            dataKey="x" 
                            name="x" 
                          />
                          <YAxis 
                            type="number" 
                            dataKey="y" 
                            name="y" 
                          />
                          <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                          <Scatter 
                            name="Values" 
                            data={analyticsResults.data} 
                            fill="#010100" 
                          />
                        </ScatterChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
              
              {/* Diagnostic Analytics Tab */}
              <TabsContent value="diagnostic">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Correlation Analysis</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="p-4 bg-muted rounded-md">
                        <p className="font-semibold mb-1">Correlation Coefficient</p>
                        <p className="text-2xl font-bold">
                          {formatNumber(analyticsResults.diagnostic.correlation)}
                        </p>
                        <p className="text-sm text-muted-foreground mt-2">
                          {analyticsResults.diagnostic.correlation > 0.7 
                            ? 'Strong positive correlation' 
                            : analyticsResults.diagnostic.correlation < -0.7 
                              ? 'Strong negative correlation' 
                              : analyticsResults.diagnostic.correlation > 0.3 
                                ? 'Moderate positive correlation' 
                                : analyticsResults.diagnostic.correlation < -0.3 
                                  ? 'Moderate negative correlation' 
                                  : 'Weak or no correlation'}
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardHeader>
                      <CardTitle>Linear Regression</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="grid grid-cols-3 gap-4">
                          <div className="stat-card">
                            <p className="text-sm text-muted-foreground">Slope</p>
                            <p className="text-xl font-semibold">
                              {formatNumber(analyticsResults.diagnostic.regression.slope)}
                            </p>
                          </div>
                          <div className="stat-card">
                            <p className="text-sm text-muted-foreground">Intercept</p>
                            <p className="text-xl font-semibold">
                              {formatNumber(analyticsResults.diagnostic.regression.intercept)}
                            </p>
                          </div>
                          <div className="stat-card">
                            <p className="text-sm text-muted-foreground">R²</p>
                            <p className="text-xl font-semibold">
                              {formatNumber(analyticsResults.diagnostic.regression.r2)}
                            </p>
                          </div>
                        </div>
                        
                        <div className="p-3 bg-muted rounded-md">
                          <p className="text-sm font-medium">Regression Equation</p>
                          <p className="mt-1 font-mono">
                            y = {formatNumber(analyticsResults.diagnostic.regression.slope)}x + {formatNumber(analyticsResults.diagnostic.regression.intercept)}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card className="lg:col-span-2">
                    <CardHeader>
                      <CardTitle>Regression Plot</CardTitle>
                    </CardHeader>
                    <CardContent className="h-60">
                      <ResponsiveContainer width="100%" height="100%">
                        <ScatterChart>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis type="number" dataKey="x" name="x" />
                          <YAxis type="number" dataKey="y" name="y" />
                          <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                          <Scatter 
                            name="Data Points" 
                            data={analyticsResults.data} 
                            fill="#010100" 
                          />
                          {/* Add regression line */}
                          <Line
                            name="Regression Line"
                            data={[
                              {
                                x: 0,
                                y: analyticsResults.diagnostic.regression.intercept
                              },
                              {
                                x: 50,
                                y: analyticsResults.diagnostic.regression.intercept + 
                                   analyticsResults.diagnostic.regression.slope * 50
                              }
                            ]}
                            type="linear"
                            dataKey="y"
                            stroke="#B5792E"
                            strokeWidth={2}
                            dot={false}
                          />
                        </ScatterChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
              
              {/* Predictive Analytics Tab */}
              <TabsContent value="predictive">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <Card className="lg:col-span-2">
                    <CardHeader>
                      <CardTitle>Forecast Models</CardTitle>
                    </CardHeader>
                    <CardContent className="h-60">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis 
                            type="number" 
                            dataKey="x" 
                            domain={['dataMin', 'dataMax + 5']}
                          />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Line
                            name="Historical Data"
                            data={analyticsResults.data}
                            type="monotone"
                            dataKey="y"
                            stroke="#010100"
                            strokeWidth={2}
                            dot={{ r: 1 }}
                            activeDot={{ r: 5 }}
                          />
                          <Line
                            name="Moving Average Forecast"
                            data={analyticsResults.predictive.movingAverageForecast}
                            type="monotone"
                            dataKey="y"
                            stroke="#B5792E"
                            strokeWidth={2}
                            strokeDasharray="5 5"
                          />
                          <Line
                            name="Regression Forecast"
                            data={analyticsResults.predictive.regressionForecast}
                            type="monotone"
                            dataKey="y"
                            stroke="#00BFFF"
                            strokeWidth={2}
                            strokeDasharray="3 3"
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardHeader>
                      <CardTitle>Moving Average Forecast</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <p className="text-sm text-muted-foreground">
                          5-period forecast based on 3-period moving average
                        </p>
                        
                        <div className="overflow-x-auto">
                          <table className="w-full min-w-[400px] border-collapse">
                            <thead>
                              <tr className="border-b">
                                <th className="text-left p-2">Period</th>
                                <th className="text-right p-2">Forecast Value</th>
                              </tr>
                            </thead>
                            <tbody>
                              {analyticsResults.predictive.movingAverageForecast.map((point: any, i: number) => (
                                <tr key={i} className="border-b">
                                  <td className="p-2">t+{i+1}</td>
                                  <td className="text-right p-2">{formatNumber(point.y)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardHeader>
                      <CardTitle>Regression Forecast</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <p className="text-sm text-muted-foreground">
                          5-period forecast based on linear regression model
                        </p>
                        
                        <div className="p-3 bg-muted rounded-md">
                          <p className="text-sm font-medium">Model Equation</p>
                          <p className="mt-1 font-mono">
                            y = {formatNumber(analyticsResults.diagnostic.regression.slope)}x + {formatNumber(analyticsResults.diagnostic.regression.intercept)}
                          </p>
                        </div>
                        
                        <div className="overflow-x-auto">
                          <table className="w-full min-w-[400px] border-collapse">
                            <thead>
                              <tr className="border-b">
                                <th className="text-left p-2">Period</th>
                                <th className="text-right p-2">Forecast Value</th>
                              </tr>
                            </thead>
                            <tbody>
                              {analyticsResults.predictive.regressionForecast.map((point: any, i: number) => (
                                <tr key={i} className="border-b">
                                  <td className="p-2">t+{i+1}</td>
                                  <td className="text-right p-2">{formatNumber(point.y)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
              
              {/* Prescriptive Analytics Tab */}
              <TabsContent value="prescriptive">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Linear Optimization</CardTitle>
                      <CardDescription>Maximize 3x + 4y subject to constraints</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="p-3 bg-muted rounded-md">
                          <p className="text-sm font-medium">Constraints</p>
                          <ul className="mt-1 space-y-1 font-mono text-sm">
                            <li>x + y ≤ 10</li>
                            <li>x ≤ 6</li>
                            <li>y ≤ 8</li>
                            <li>x, y ≥ 0</li>
                          </ul>
                        </div>
                        
                        <div className="p-3 border rounded-md">
                          <div className="flex justify-between items-center mb-2">
                            <p className="font-medium">Optimal Solution</p>
                            <p className="text-savvy-gold font-bold">
                              {analyticsResults.prescriptive.optimizationResult.optimalPoint ? 
                                `Value: ${formatNumber(analyticsResults.prescriptive.optimizationResult.optimalValue)}` : 'No solution found'}
                            </p>
                          </div>
                          {analyticsResults.prescriptive.optimizationResult.optimalPoint && (
                            <p>
                              x = {formatNumber(analyticsResults.prescriptive.optimizationResult.optimalPoint[0])},
                              y = {formatNumber(analyticsResults.prescriptive.optimizationResult.optimalPoint[1])}
                            </p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card className="lg:row-span-2">
                    <CardHeader>
                      <CardTitle>Scenario Analysis</CardTitle>
                      <CardDescription>Decision tree based recommendations</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <table className="w-full min-w-[500px] border-collapse">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left p-2">Scenario</th>
                              <th className="text-left p-2">Option</th>
                              <th className="text-right p-2">Cost</th>
                              <th className="text-right p-2">Benefit</th>
                              <th className="text-right p-2">ROI</th>
                              <th className="text-left p-2">Recommendation</th>
                            </tr>
                          </thead>
                          <tbody>
                            {analyticsResults.prescriptive.scenarioAnalysis.map((scenario: any, i: number) => (
                              <tr key={i} className="border-b">
                                <td className="p-2">{scenario.name}</td>
                                <td className="p-2">{scenario.option}</td>
                                <td className="text-right p-2">${scenario.cost.toLocaleString()}</td>
                                <td className="text-right p-2">${scenario.benefit.toLocaleString()}</td>
                                <td className={`text-right p-2 ${
                                  scenario.roi >= 50 ? 'text-green-600' : 
                                  scenario.roi >= 20 ? 'text-amber-600' : 
                                  scenario.roi >= 0 ? 'text-blue-600' : 'text-red-600'
                                }`}>
                                  {formatNumber(scenario.roi)}%
                                </td>
                                <td className={`p-2 ${
                                  scenario.recommendation === 'Highly Recommended' ? 'text-green-600' :
                                  scenario.recommendation === 'Recommended' ? 'text-amber-600' :
                                  scenario.recommendation === 'Consider' ? 'text-blue-600' : 'text-red-600'
                                }`}>
                                  {scenario.recommendation}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardHeader>
                      <CardTitle>Expected Value Analysis</CardTitle>
                      <CardDescription>Incorporating probability into decisions</CardDescription>
                    </CardHeader>
                    <CardContent className="h-60">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={analyticsResults.prescriptive.scenarioAnalysis}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis />
                          <Tooltip formatter={(value) => [`$${parseInt(value).toLocaleString()}`, 'Expected Value']} />
                          <Bar dataKey="expectedValue" name="Expected Value" fill="#B5792E" />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
            </Tabs>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AnalyticsModelsTest;
