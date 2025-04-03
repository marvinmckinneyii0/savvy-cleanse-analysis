
/**
 * Analytics Models Utility
 * 
 * This file contains basic implementations of descriptive, diagnostic,
 * predictive, and prescriptive analytics models for testing the application.
 */

// Sample data interface
export interface DataPoint {
  x: number;
  y: number;
  category?: string;
  date?: Date;
  value?: number;
}

/**
 * DESCRIPTIVE ANALYTICS
 * Summarizes historical data through statistics
 */
export const descriptiveAnalytics = {
  // Calculate basic summary statistics
  calculateSummaryStats: (data: DataPoint[]) => {
    if (!data.length) return { mean: 0, median: 0, mode: 0, stdDev: 0 };
    
    // Mean calculation
    const sum = data.reduce((acc, point) => acc + point.y, 0);
    const mean = sum / data.length;
    
    // Median calculation
    const sortedValues = [...data].sort((a, b) => a.y - b.y);
    const middle = Math.floor(sortedValues.length / 2);
    const median = sortedValues.length % 2 === 0
      ? (sortedValues[middle - 1].y + sortedValues[middle].y) / 2
      : sortedValues[middle].y;
    
    // Mode calculation (most frequent value)
    const valueFrequency: Record<number, number> = {};
    data.forEach(point => {
      valueFrequency[point.y] = (valueFrequency[point.y] || 0) + 1;
    });
    
    let mode = data[0].y;
    let maxFrequency = 0;
    Object.entries(valueFrequency).forEach(([value, frequency]) => {
      if (frequency > maxFrequency) {
        maxFrequency = frequency;
        mode = parseFloat(value);
      }
    });
    
    // Standard Deviation
    const squareDiffs = data.map(point => Math.pow(point.y - mean, 2));
    const avgSquareDiff = squareDiffs.reduce((acc, val) => acc + val, 0) / data.length;
    const stdDev = Math.sqrt(avgSquareDiff);
    
    return { mean, median, mode, stdDev };
  },
  
  // Create frequency distribution
  generateFrequencyDistribution: (data: DataPoint[], bins: number = 10) => {
    if (!data.length) return [];
    
    const yValues = data.map(point => point.y);
    const min = Math.min(...yValues);
    const max = Math.max(...yValues);
    const range = max - min;
    const binWidth = range / bins;
    
    const distribution = Array(bins).fill(0);
    
    data.forEach(point => {
      const binIndex = Math.min(
        Math.floor((point.y - min) / binWidth),
        bins - 1
      );
      distribution[binIndex]++;
    });
    
    return distribution.map((count, i) => ({
      binStart: min + i * binWidth,
      binEnd: min + (i + 1) * binWidth,
      count,
    }));
  },
};

/**
 * DIAGNOSTIC ANALYTICS
 * Identifies patterns and relationships in the data
 */
export const diagnosticAnalytics = {
  // Calculate correlation between x and y
  calculateCorrelation: (data: DataPoint[]) => {
    if (data.length < 2) return 0;
    
    const n = data.length;
    
    // Calculate means
    const meanX = data.reduce((sum, point) => sum + point.x, 0) / n;
    const meanY = data.reduce((sum, point) => sum + point.y, 0) / n;
    
    // Calculate covariance and variances
    let covariance = 0;
    let varianceX = 0;
    let varianceY = 0;
    
    for (const point of data) {
      const diffX = point.x - meanX;
      const diffY = point.y - meanY;
      covariance += diffX * diffY;
      varianceX += diffX * diffX;
      varianceY += diffY * diffY;
    }
    
    if (varianceX === 0 || varianceY === 0) return 0;
    
    return covariance / Math.sqrt(varianceX * varianceY);
  },
  
  // Simple linear regression
  linearRegression: (data: DataPoint[]) => {
    if (data.length < 2) return { slope: 0, intercept: 0, r2: 0 };
    
    const n = data.length;
    
    // Calculate means
    const meanX = data.reduce((sum, point) => sum + point.x, 0) / n;
    const meanY = data.reduce((sum, point) => sum + point.y, 0) / n;
    
    // Calculate coefficients
    let numerator = 0;
    let denominator = 0;
    
    for (const point of data) {
      const diffX = point.x - meanX;
      numerator += diffX * (point.y - meanY);
      denominator += diffX * diffX;
    }
    
    const slope = denominator !== 0 ? numerator / denominator : 0;
    const intercept = meanY - slope * meanX;
    
    // Calculate R-squared
    const predictions = data.map(point => intercept + slope * point.x);
    const residualSumOfSquares = data.reduce((sum, point, i) => 
      sum + Math.pow(point.y - predictions[i], 2), 0);
    const totalSumOfSquares = data.reduce((sum, point) => 
      sum + Math.pow(point.y - meanY, 2), 0);
    
    const r2 = totalSumOfSquares !== 0 ? 1 - residualSumOfSquares / totalSumOfSquares : 0;
    
    return { slope, intercept, r2 };
  },
};

/**
 * PREDICTIVE ANALYTICS
 * Forecasts future trends based on historical data
 */
export const predictiveAnalytics = {
  // Simple moving average forecast
  movingAverageForecast: (data: DataPoint[], window: number = 3, periods: number = 5) => {
    if (data.length < window) return [];
    
    const sortedData = [...data].sort((a, b) => a.x - b.x);
    const yValues = sortedData.map(point => point.y);
    
    // Calculate historical moving averages
    const movingAverages = [];
    for (let i = window - 1; i < yValues.length; i++) {
      const windowSum = yValues.slice(i - window + 1, i + 1).reduce((sum, val) => sum + val, 0);
      movingAverages.push(windowSum / window);
    }
    
    // Generate forecast
    const forecast = [];
    let lastX = sortedData[sortedData.length - 1].x;
    let lastWindowValues = yValues.slice(yValues.length - window);
    
    for (let i = 1; i <= periods; i++) {
      const windowSum = lastWindowValues.reduce((sum, val) => sum + val, 0);
      const nextValue = windowSum / window;
      
      forecast.push({
        x: lastX + i,
        y: nextValue,
        isForecast: true
      });
      
      lastWindowValues.shift();
      lastWindowValues.push(nextValue);
    }
    
    return forecast;
  },
  
  // Simple linear regression forecast
  linearRegressionForecast: (data: DataPoint[], periodsAhead: number = 5) => {
    const { slope, intercept } = diagnosticAnalytics.linearRegression(data);
    
    // Find the last x value
    const lastX = Math.max(...data.map(point => point.x));
    
    // Generate forecasts
    const forecasts = [];
    for (let i = 1; i <= periodsAhead; i++) {
      const forecastX = lastX + i;
      forecasts.push({
        x: forecastX,
        y: intercept + slope * forecastX,
        isForecast: true
      });
    }
    
    return forecasts;
  },
  
  // Calculate forecast accuracy
  calculateAccuracy: (actualValues: number[], predictedValues: number[]) => {
    if (actualValues.length !== predictedValues.length || actualValues.length === 0) {
      return { mape: 0, rmse: 0 };
    }
    
    let sumPercentErrors = 0;
    let sumSquaredErrors = 0;
    
    for (let i = 0; i < actualValues.length; i++) {
      const actual = actualValues[i];
      const predicted = predictedValues[i];
      const error = actual - predicted;
      
      // Mean Absolute Percentage Error
      if (actual !== 0) {
        sumPercentErrors += Math.abs(error / actual);
      }
      
      // Root Mean Square Error
      sumSquaredErrors += error * error;
    }
    
    const mape = (sumPercentErrors / actualValues.length) * 100;
    const rmse = Math.sqrt(sumSquaredErrors / actualValues.length);
    
    return { mape, rmse };
  },
};

/**
 * PRESCRIPTIVE ANALYTICS
 * Suggests optimal decisions based on predicted outcomes
 */
export const prescriptiveAnalytics = {
  // Simple optimization for two variables with linear constraints
  simplexOptimization: (
    objectiveCoeffs: [number, number],  // Coefficients for the objective function to maximize
    constraints: Array<{ coeffs: [number, number], rhs: number }> // Constraints in the form ax + by ≤ c
  ) => {
    // This is a very simplified version of the simplex algorithm
    // It works by checking the corner points of the feasible region
    
    // First, find the intersection points of all constraints with both axes
    const points: [number, number][] = [
      [0, 0] // Origin is always a candidate
    ];
    
    // Add intersections with x-axis (y = 0)
    constraints.forEach(constraint => {
      if (constraint.coeffs[0] !== 0) {
        const x = constraint.rhs / constraint.coeffs[0];
        if (x >= 0) {
          points.push([x, 0]);
        }
      }
    });
    
    // Add intersections with y-axis (x = 0)
    constraints.forEach(constraint => {
      if (constraint.coeffs[1] !== 0) {
        const y = constraint.rhs / constraint.coeffs[1];
        if (y >= 0) {
          points.push([0, y]);
        }
      }
    });
    
    // Add intersections of constraints with each other
    for (let i = 0; i < constraints.length; i++) {
      for (let j = i + 1; j < constraints.length; j++) {
        const a1 = constraints[i].coeffs[0];
        const b1 = constraints[i].coeffs[1];
        const c1 = constraints[i].rhs;
        
        const a2 = constraints[j].coeffs[0];
        const b2 = constraints[j].coeffs[1];
        const c2 = constraints[j].rhs;
        
        // Calculate determinant to check if lines are parallel
        const det = a1 * b2 - a2 * b1;
        
        if (det !== 0) {
          const x = (c1 * b2 - c2 * b1) / det;
          const y = (a1 * c2 - a2 * c1) / det;
          
          if (x >= 0 && y >= 0) {
            points.push([x, y]);
          }
        }
      }
    }
    
    // Filter points that satisfy all constraints
    const feasiblePoints = points.filter(([x, y]) => {
      return constraints.every(constraint => {
        const leftSide = constraint.coeffs[0] * x + constraint.coeffs[1] * y;
        return leftSide <= constraint.rhs;
      });
    });
    
    // Evaluate objective function at each feasible point
    let bestValue = -Infinity;
    let optimalPoint: [number, number] | null = null;
    
    feasiblePoints.forEach(([x, y]) => {
      const objectiveValue = objectiveCoeffs[0] * x + objectiveCoeffs[1] * y;
      if (objectiveValue > bestValue) {
        bestValue = objectiveValue;
        optimalPoint = [x, y];
      }
    });
    
    return {
      optimalPoint,
      optimalValue: bestValue,
      feasiblePoints
    };
  },
  
  // Decision tree for scenario analysis (very simplified)
  decisionTree: (
    scenarios: Array<{
      name: string;
      option: string;
      cost: number;
      benefit: number;
      probability?: number;
    }>
  ) => {
    return scenarios.map(scenario => {
      const roi = ((scenario.benefit - scenario.cost) / scenario.cost) * 100;
      const expectedValue = scenario.probability 
        ? (scenario.benefit - scenario.cost) * scenario.probability
        : scenario.benefit - scenario.cost;
      
      return {
        ...scenario,
        roi,
        expectedValue,
        recommendation: roi >= 50 ? 'Highly Recommended' :
          roi >= 20 ? 'Recommended' :
          roi >= 0 ? 'Consider' : 'Avoid'
      };
    }).sort((a, b) => b.expectedValue - a.expectedValue);
  }
};

// Generate sample data for testing
export const generateSampleData = (numPoints: number = 50): DataPoint[] => {
  const data: DataPoint[] = [];
  
  for (let i = 0; i < numPoints; i++) {
    // Generate x with some randomness, but generally increasing
    const x = i + Math.random() * 0.5;
    
    // Generate y with linear relationship to x plus noise
    // y = 2x + 5 + noise
    const noise = Math.random() * 10 - 5; // Random noise between -5 and 5
    const y = 2 * x + 5 + noise;
    
    // Add date (for time series)
    const date = new Date();
    date.setDate(date.getDate() + i);
    
    // Assign a random category
    const categories = ['A', 'B', 'C', 'D'];
    const category = categories[Math.floor(Math.random() * categories.length)];
    
    data.push({
      x,
      y,
      date,
      category,
      value: y // Alias for charts that use 'value' instead of 'y'
    });
  }
  
  return data;
};

// Function to apply each type of analytics to sample data
export const runAllAnalytics = () => {
  const sampleData = generateSampleData(50);
  
  // Run descriptive analytics
  const summaryStats = descriptiveAnalytics.calculateSummaryStats(sampleData);
  const frequencyDistribution = descriptiveAnalytics.generateFrequencyDistribution(sampleData, 10);
  
  // Run diagnostic analytics
  const correlation = diagnosticAnalytics.calculateCorrelation(sampleData);
  const regression = diagnosticAnalytics.linearRegression(sampleData);
  
  // Run predictive analytics
  const movingAverageForecast = predictiveAnalytics.movingAverageForecast(sampleData, 3, 5);
  const regressionForecast = predictiveAnalytics.linearRegressionForecast(sampleData, 5);
  
  // Run prescriptive analytics - simple example
  const optimizationResult = prescriptiveAnalytics.simplexOptimization(
    [3, 4], // Maximize 3x + 4y
    [
      { coeffs: [1, 1], rhs: 10 }, // x + y ≤ 10
      { coeffs: [1, 0], rhs: 6 },  // x ≤ 6
      { coeffs: [0, 1], rhs: 8 },  // y ≤ 8
    ]
  );
  
  const scenarioAnalysis = prescriptiveAnalytics.decisionTree([
    { name: 'Scenario A', option: 'Option 1', cost: 25000, benefit: 45000, probability: 0.7 },
    { name: 'Scenario B', option: 'Option 2', cost: 15000, benefit: 22500, probability: 0.8 },
    { name: 'Scenario C', option: 'Option 3', cost: 40000, benefit: 50000, probability: 0.5 },
  ]);
  
  return {
    data: sampleData,
    descriptive: { summaryStats, frequencyDistribution },
    diagnostic: { correlation, regression },
    predictive: { movingAverageForecast, regressionForecast },
    prescriptive: { optimizationResult, scenarioAnalysis }
  };
};
