import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Calendar, Filter, RotateCcw } from 'lucide-react';

interface FilterState {
  dateRange: string;
  region: string;
  category: string;
  customFilter: string;
}

interface DashboardFiltersProps {
  filters: FilterState;
  onFilterChange: (key: keyof FilterState, value: string) => void;
  onApplyFilters: () => void;
  onResetFilters: () => void;
  loading?: boolean;
}

const DashboardFilters: React.FC<DashboardFiltersProps> = ({
  filters,
  onFilterChange,
  onApplyFilters,
  onResetFilters,
  loading = false
}) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Filter className="h-5 w-5" />
          Filters & Controls
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="space-y-2">
            <Label htmlFor="dateRange" className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              Date Range
            </Label>
            <Select 
              value={filters.dateRange} 
              onValueChange={(value) => onFilterChange('dateRange', value)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="last_7_days">Last 7 days</SelectItem>
                <SelectItem value="last_30_days">Last 30 days</SelectItem>
                <SelectItem value="last_90_days">Last 90 days</SelectItem>
                <SelectItem value="last_year">Last year</SelectItem>
                <SelectItem value="custom">Custom range</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="region">Region</Label>
            <Select 
              value={filters.region} 
              onValueChange={(value) => onFilterChange('region', value)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Regions</SelectItem>
                <SelectItem value="north_america">North America</SelectItem>
                <SelectItem value="europe">Europe</SelectItem>
                <SelectItem value="asia_pacific">Asia Pacific</SelectItem>
                <SelectItem value="latin_america">Latin America</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="category">Category</Label>
            <Select 
              value={filters.category} 
              onValueChange={(value) => onFilterChange('category', value)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="product_a">Product A</SelectItem>
                <SelectItem value="product_b">Product B</SelectItem>
                <SelectItem value="product_c">Product C</SelectItem>
                <SelectItem value="product_d">Product D</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="customFilter">Custom Filter</Label>
            <Input 
              id="customFilter"
              placeholder="Enter filter value..."
              value={filters.customFilter}
              onChange={(e) => onFilterChange('customFilter', e.target.value)}
            />
          </div>

          <div className="flex flex-col gap-2">
            <Button 
              onClick={onApplyFilters}
              disabled={loading}
              className="bg-savvy-blue hover:bg-savvy-blue/90"
            >
              Apply Filters
            </Button>
            <Button 
              variant="outline"
              onClick={onResetFilters}
              size="sm"
            >
              <RotateCcw className="h-3 w-3 mr-1" />
              Reset
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default DashboardFilters;