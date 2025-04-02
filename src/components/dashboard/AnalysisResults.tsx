
import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface AnalysisResultsProps {
  analysisType: string;
  // In a real app, you would have more specific typing for the data
  data: any;
}

const AnalysisResults: React.FC<AnalysisResultsProps> = ({ analysisType, data }) => {
  // In a real app, this would be dynamic based on the actual data and analysis results
  // For this demo, we're showing static examples for each analysis type
  
  const renderDescriptiveAnalysis = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Summary Statistics</CardTitle>
          <CardDescription>Key metrics for your dataset</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="stat-card">
              <p className="text-sm text-muted-foreground">Mean</p>
              <p className="text-2xl font-semibold">42.8</p>
            </div>
            <div className="stat-card">
              <p className="text-sm text-muted-foreground">Median</p>
              <p className="text-2xl font-semibold">38.5</p>
            </div>
            <div className="stat-card">
              <p className="text-sm text-muted-foreground">Mode</p>
              <p className="text-2xl font-semibold">36.0</p>
            </div>
            <div className="stat-card">
              <p className="text-sm text-muted-foreground">Std. Deviation</p>
              <p className="text-2xl font-semibold">12.3</p>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Frequency Distribution</CardTitle>
          <CardDescription>Histogram visualization</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-60 w-full bg-muted rounded-md flex items-center justify-center">
            <p className="text-muted-foreground text-sm">
              Histogram visualization would appear here
            </p>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Key Formulas</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-sm text-muted-foreground mb-1">Mean (Average)</p>
            <div className="formula-block">
              <code>μ = (Σxᵢ)/n</code>
            </div>
          </div>
          <div>
            <p className="text-sm text-muted-foreground mb-1">Standard Deviation</p>
            <div className="formula-block">
              <code>σ = sqrt(Σ(xᵢ - μ)² / n)</code>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Python Code</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="code-block">
{`import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Calculate summary statistics
mean = df['value'].mean()
median = df['value'].median()
std_dev = df['value'].std()

# Create histogram
plt.figure(figsize=(10, 6))
plt.hist(df['value'], bins=20, alpha=0.7)
plt.title('Frequency Distribution')
plt.xlabel('Value')
plt.ylabel('Frequency')
plt.grid(alpha=0.3)
plt.show()

# Display summary
print(f"Mean: {mean:.2f}")
print(f"Median: {median:.2f}")
print(f"Standard Deviation: {std_dev:.2f}")
`}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
  
  const renderDiagnosticAnalysis = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Correlation Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-60 w-full bg-muted rounded-md flex items-center justify-center">
            <p className="text-muted-foreground text-sm">
              Correlation heatmap would appear here
            </p>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Regression Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-60 w-full bg-muted rounded-md flex items-center justify-center">
            <p className="text-muted-foreground text-sm">
              Regression plot would appear here
            </p>
          </div>
          
          <div className="mt-4 grid grid-cols-2 gap-4">
            <div className="stat-card">
              <p className="text-sm text-muted-foreground">R-squared</p>
              <p className="text-2xl font-semibold">0.876</p>
            </div>
            <div className="stat-card">
              <p className="text-sm text-muted-foreground">p-value</p>
              <p className="text-2xl font-semibold">0.002</p>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Key Formulas</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-sm text-muted-foreground mb-1">Correlation</p>
            <div className="formula-block">
              <code>r = Σ[(xᵢ - x̄)(yᵢ - ȳ)] / √[Σ(xᵢ - x̄)²Σ(yᵢ - ȳ)²]</code>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Python Code</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="code-block">
{`import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats

# Correlation analysis
corr_matrix = df.corr()
plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
plt.title('Correlation Matrix')
plt.show()

# Linear regression
x = df['feature']
y = df['target']
slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

# Plot regression line
plt.figure(figsize=(10, 6))
plt.scatter(x, y, alpha=0.7)
plt.plot(x, intercept + slope*x, 'r')
plt.title('Linear Regression')
plt.xlabel('Feature')
plt.ylabel('Target')
plt.grid(alpha=0.3)
plt.show()

print(f"R-squared: {r_value**2:.3f}")
print(f"p-value: {p_value:.3f}")
`}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
  
  const renderPredictiveAnalysis = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Forecast Model</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-60 w-full bg-muted rounded-md flex items-center justify-center">
            <p className="text-muted-foreground text-sm">
              Time series forecast plot would appear here
            </p>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Model Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="stat-card">
              <p className="text-sm text-muted-foreground">Accuracy</p>
              <p className="text-2xl font-semibold">92.4%</p>
            </div>
            <div className="stat-card">
              <p className="text-sm text-muted-foreground">Precision</p>
              <p className="text-2xl font-semibold">0.88</p>
            </div>
            <div className="stat-card">
              <p className="text-sm text-muted-foreground">Recall</p>
              <p className="text-2xl font-semibold">0.91</p>
            </div>
            <div className="stat-card">
              <p className="text-sm text-muted-foreground">F1 Score</p>
              <p className="text-2xl font-semibold">0.89</p>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Key Formulas</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-sm text-muted-foreground mb-1">Linear Regression</p>
            <div className="formula-block">
              <code>ŷ = β₀ + β₁X</code>
            </div>
          </div>
          <div>
            <p className="text-sm text-muted-foreground mb-1">Logistic Regression</p>
            <div className="formula-block">
              <code>P(Y=1) = 1 / (1 + e^-(β₀ + β₁X))</code>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Python Code</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="code-block">
{`import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Train model
model = LogisticRegression()
model.fit(X_train, y_train)

# Make predictions
y_pred = model.predict(X_test)

# Evaluate model
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)

print(f"Accuracy: {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1 Score: {f1:.4f}")
`}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
  
  const renderPrescriptiveAnalysis = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Optimization Model</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-60 w-full bg-muted rounded-md flex items-center justify-center">
            <p className="text-muted-foreground text-sm">
              Decision tree visualization would appear here
            </p>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Scenario Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[600px]">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Scenario</th>
                  <th className="text-left p-2">Outcome</th>
                  <th className="text-left p-2">Cost</th>
                  <th className="text-left p-2">Benefit</th>
                  <th className="text-left p-2">ROI</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b">
                  <td className="p-2">Scenario A</td>
                  <td className="p-2">Option 1</td>
                  <td className="p-2">$25,000</td>
                  <td className="p-2">$45,000</td>
                  <td className="p-2 text-green-600">80%</td>
                </tr>
                <tr className="border-b">
                  <td className="p-2">Scenario B</td>
                  <td className="p-2">Option 2</td>
                  <td className="p-2">$15,000</td>
                  <td className="p-2">$22,500</td>
                  <td className="p-2 text-green-600">50%</td>
                </tr>
                <tr className="border-b">
                  <td className="p-2">Scenario C</td>
                  <td className="p-2">Option 3</td>
                  <td className="p-2">$40,000</td>
                  <td className="p-2">$50,000</td>
                  <td className="p-2 text-green-600">25%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Key Formulas</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-sm text-muted-foreground mb-1">Objective Function</p>
            <div className="formula-block">
              <code>Max Z = c₁x₁ + c₂x₂ ...</code>
            </div>
          </div>
          <div>
            <p className="text-sm text-muted-foreground mb-1">Constraints</p>
            <div className="formula-block">
              <code>a₁x₁ + a₂x₂ ≤ b</code>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Python Code</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="code-block">
{`import numpy as np
from scipy.optimize import linprog
import matplotlib.pyplot as plt
from sklearn.tree import DecisionTreeClassifier, plot_tree

# Linear programming optimization
# Maximize: Z = 5x + 7y
# Subject to: 2x + 3y ≤ 20
#             4x + 2y ≤ 15
#             x, y ≥ 0

# Negative coefficients for maximization problem
c = [-5, -7]  
A = [[2, 3], [4, 2]]
b = [20, 15]

# Solve linear programming problem
res = linprog(c, A_ub=A, b_ub=b, bounds=(0, None))

print("Optimal solution:")
print(f"x = {res.x[0]:.2f}, y = {res.x[1]:.2f}")
print(f"Optimal value: {-res.fun:.2f}")

# Decision tree for scenario analysis
model = DecisionTreeClassifier(max_depth=3)
model.fit(X_train, y_train)

plt.figure(figsize=(15, 10))
plot_tree(model, filled=True, feature_names=feature_names, class_names=class_names)
plt.title('Decision Tree for Scenario Analysis')
plt.show()
`}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
  
  const renderAnalysisContent = () => {
    switch (analysisType) {
      case 'descriptive':
        return renderDescriptiveAnalysis();
      case 'diagnostic':
        return renderDiagnosticAnalysis();
      case 'predictive':
        return renderPredictiveAnalysis();
      case 'prescriptive':
        return renderPrescriptiveAnalysis();
      default:
        return (
          <div className="text-center p-8">
            <p className="text-muted-foreground">Select an analysis type to see results</p>
          </div>
        );
    }
  };
  
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">{analysisType.charAt(0).toUpperCase() + analysisType.slice(1)} Analysis Results</h2>
      
      <Tabs defaultValue="visualizations">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="visualizations">Visualizations</TabsTrigger>
          <TabsTrigger value="formulas">Formulas</TabsTrigger>
          <TabsTrigger value="code">Python Code</TabsTrigger>
        </TabsList>
        
        <TabsContent value="visualizations" className="mt-4">
          {renderAnalysisContent()}
        </TabsContent>
        
        <TabsContent value="formulas" className="mt-4">
          {renderAnalysisContent()}
        </TabsContent>
        
        <TabsContent value="code" className="mt-4">
          {renderAnalysisContent()}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AnalysisResults;
