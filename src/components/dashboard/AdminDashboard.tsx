import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Users, 
  Database, 
  BarChart3, 
  Activity, 
  AlertTriangle,
  Calendar,
  Shield,
  TrendingUp,
  FileText,
  Brain,
  Settings
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  created_at: string;
}

interface SystemStats {
  total_users: number;
  total_datasets: number;
  total_analyses: number;
}

interface ActivityLog {
  id: string;
  user_id: string;
  action: string;
  status: string;
  created_at: string;
  error_message?: string;
  metadata?: any;
}

interface AdminDashboardData {
  system_stats: SystemStats;
  users: User[];
  recent_activity: ActivityLog[];
  user_activity_summary: Record<string, number>;
}

const AdminDashboard: React.FC = () => {
  // Mock admin user data since auth is removed
  const user = { email: 'admin@example.com' };
  const session = { access_token: 'mock-admin-token' };
  const isAdmin = true;
  const { toast } = useToast();
  
  const [dashboardData, setDashboardData] = useState<AdminDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState<string>('');

  useEffect(() => {
    // Always fetch data since we're using mock data
    fetchAdminData();
  }, []);

  const fetchAdminData = async () => {
    try {
      // For now, use mock data since auth is disabled
      const mockData = {
        system_stats: {
          total_users: 15,
          total_datasets: 42,
          total_analyses: 128
        },
        users: [
          {
            id: "1",
            email: "admin@example.com",
            full_name: "Admin User",
            role: "admin",
            created_at: new Date(Date.now() - 86400000 * 30).toISOString()
          },
          {
            id: "2",
            email: "user1@example.com", 
            full_name: "John Doe",
            role: "user",
            created_at: new Date(Date.now() - 86400000 * 15).toISOString()
          },
          {
            id: "3",
            email: "user2@example.com",
            full_name: "Jane Smith", 
            role: "user",
            created_at: new Date(Date.now() - 86400000 * 7).toISOString()
          }
        ],
        recent_activity: [
          {
            id: "1",
            user_id: "2",
            action: "file_upload",
            status: "success",
            created_at: new Date().toISOString(),
            metadata: { filename: "sales_data.csv", dataset_id: "abc123" }
          },
          {
            id: "2",
            user_id: "3", 
            action: "descriptive_analysis",
            status: "success",
            created_at: new Date(Date.now() - 3600000).toISOString(),
            metadata: { dataset_id: "def456" }
          },
          {
            id: "3",
            user_id: "2",
            action: "nlp_query", 
            status: "error",
            created_at: new Date(Date.now() - 7200000).toISOString(),
            error_message: "API key not configured",
            metadata: { dataset_id: "ghi789" }
          }
        ],
        user_activity_summary: {
          "1": 5,
          "2": 12,
          "3": 8
        }
      };
      
      setDashboardData(mockData);
    } catch (error) {
      console.error('Error fetching admin data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load admin dashboard data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const updateUserRole = async (userId: string, newRole: string) => {
    try {
      // For now, just show success message with mock data
      toast({
        title: 'Success',
        description: 'User role updated successfully',
      });
      
      // Update the local mock data
      if (dashboardData) {
        const updatedUsers = dashboardData.users.map(user => 
          user.id === userId ? { ...user, role: newRole } : user
        );
        setDashboardData({
          ...dashboardData,
          users: updatedUsers
        });
      }
    } catch (error) {
      console.error('Error updating user role:', error);
      toast({
        title: 'Error',
        description: 'Failed to update user role',
        variant: 'destructive',
      });
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'bg-green-500';
      case 'error': return 'bg-red-500';
      case 'pending': return 'bg-yellow-500';
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

  const getActivityIcon = (action: string) => {
    switch (action) {
      case 'file_upload': return <FileText className="h-4 w-4" />;
      case 'descriptive_analysis': 
      case 'diagnostic_analysis':
      case 'predictive_analysis':
      case 'prescriptive_analysis': return <BarChart3 className="h-4 w-4" />;
      case 'nlp_query': return <Brain className="h-4 w-4" />;
      case 'data_cleaning': return <Settings className="h-4 w-4" />;
      default: return <Activity className="h-4 w-4" />;
    }
  };

  if (!isAdmin) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          You do not have admin privileges to access this dashboard.
        </AlertDescription>
      </Alert>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Activity className="mx-auto h-8 w-8 animate-spin text-muted-foreground" />
          <p className="mt-2 text-muted-foreground">Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Failed to load admin dashboard data.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Admin Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Shield className="h-8 w-8" />
            Admin Dashboard
          </h1>
          <p className="text-muted-foreground">
            System overview and user management for SavvyCleanse
          </p>
        </div>
      </div>

      {/* System Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.system_stats.total_users}</div>
            <p className="text-xs text-muted-foreground">
              Registered platform users
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Datasets</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.system_stats.total_datasets}</div>
            <p className="text-xs text-muted-foreground">
              Files uploaded across all users
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Analyses</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.system_stats.total_analyses}</div>
            <p className="text-xs text-muted-foreground">
              Analytics operations performed
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Users Management */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            User Management
          </CardTitle>
          <CardDescription>
            Manage user roles and monitor user activity
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {dashboardData.users.length === 0 ? (
              <p className="text-sm text-muted-foreground">No users found.</p>
            ) : (
              <div className="space-y-3">
                {dashboardData.users.map((user) => (
                  <div key={user.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{user.full_name || user.email}</p>
                        <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>
                          {user.role}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">{user.email}</p>
                      <p className="text-xs text-muted-foreground">
                        <Calendar className="inline h-3 w-3 mr-1" />
                        Joined {formatDate(user.created_at)}
                      </p>
                      {dashboardData.user_activity_summary[user.id] && (
                        <p className="text-xs text-muted-foreground">
                          <Activity className="inline h-3 w-3 mr-1" />
                          {dashboardData.user_activity_summary[user.id]} recent activities
                        </p>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <select
                        className="text-sm border rounded px-2 py-1"
                        value={user.role}
                        onChange={(e) => updateUserRole(user.id, e.target.value)}
                        disabled={user.id === user.id} // Can't change own role
                      >
                        <option value="user">User</option>
                        <option value="admin">Admin</option>
                      </select>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Recent System Activity
          </CardTitle>
          <CardDescription>
            Monitor user actions and system events
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {dashboardData.recent_activity.length === 0 ? (
              <p className="text-sm text-muted-foreground">No recent activity.</p>
            ) : (
              dashboardData.recent_activity.map((log) => {
                const user = dashboardData.users.find(u => u.id === log.user_id);
                return (
                  <div key={log.id} className="flex items-start gap-3 p-3 border rounded-lg">
                    <div className="mt-1">
                      {getActivityIcon(log.action)}
                    </div>
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-sm">
                          {user?.full_name || user?.email || 'Unknown User'}
                        </p>
                        <Badge className={`${getStatusColor(log.status)} text-white text-xs`}>
                          {log.status}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground capitalize">
                        {log.action.replace('_', ' ')}
                        {log.metadata?.filename && ` - ${log.metadata.filename}`}
                        {log.metadata?.dataset_id && ` (Dataset: ${log.metadata.dataset_id.slice(0, 8)}...)`}
                      </p>
                      {log.error_message && (
                        <p className="text-xs text-red-600 bg-red-50 p-2 rounded">
                          Error: {log.error_message}
                        </p>
                      )}
                      <p className="text-xs text-muted-foreground">
                        <Calendar className="inline h-3 w-3 mr-1" />
                        {formatDate(log.created_at)}
                      </p>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </CardContent>
      </Card>

      {/* User Activity Summary */}
      {Object.keys(dashboardData.user_activity_summary).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              User Activity Summary
            </CardTitle>
            <CardDescription>
              Overview of user engagement and activity levels
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(dashboardData.user_activity_summary)
                .sort(([,a], [,b]) => b - a) // Sort by activity count descending
                .map(([userId, activityCount]) => {
                  const user = dashboardData.users.find(u => u.id === userId);
                  return (
                    <div key={userId} className="flex items-center justify-between p-2 border rounded">
                      <div>
                        <p className="font-medium text-sm">{user?.full_name || user?.email || 'Unknown User'}</p>
                        <p className="text-xs text-muted-foreground">{user?.email}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-lg">{activityCount}</p>
                        <p className="text-xs text-muted-foreground">activities</p>
                      </div>
                    </div>
                  );
                })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AdminDashboard;