
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { RefreshCw, Activity, AlertCircle } from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';

interface LiveDataEntry {
  id: string;
  timestamp: string;
  source: string;
  metrics: Record<string, any>;
  raw_data: Record<string, any>;
  created_at: string;
}

const LiveDataStream: React.FC = () => {
  const [liveData, setLiveData] = useState<LiveDataEntry[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [supabaseConfigured, setSupabaseConfigured] = useState(true);

  useEffect(() => {
    // Check if Supabase is properly configured
    const checkSupabaseConfig = () => {
      const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
      const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
      
      if (!supabaseUrl || !supabaseAnonKey) {
        setSupabaseConfigured(false);
        setError('Supabase environment variables are not configured. Please check your project settings.');
        return false;
      }
      return true;
    };

    if (!checkSupabaseConfig()) {
      return;
    }

    // Set up real-time subscription
    const channel = supabase
      .channel('live_data_changes')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'live_data_stream'
        },
        (payload) => {
          console.log('New live data received:', payload);
          const newEntry = payload.new as LiveDataEntry;
          setLiveData(prev => [newEntry, ...prev.slice(0, 19)]); // Keep latest 20 entries
          setLastUpdate(new Date());
          setIsConnected(true);
          setError(null);
        }
      )
      .subscribe((status) => {
        console.log('Subscription status:', status);
        if (status === 'SUBSCRIBED') {
          setIsConnected(true);
        } else if (status === 'CLOSED') {
          setIsConnected(false);
        }
      });

    // Load initial data
    loadInitialData();

    // Set up polling as fallback (every 5 seconds)
    const pollInterval = setInterval(() => {
      if (supabaseConfigured) {
        loadInitialData();
      }
    }, 5000);

    return () => {
      if (supabaseConfigured) {
        supabase.removeChannel(channel);
      }
      clearInterval(pollInterval);
    };
  }, [supabaseConfigured]);

  const loadInitialData = async () => {
    if (!supabaseConfigured) return;
    
    try {
      const { data, error } = await supabase
        .from('live_data_stream')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(20);

      if (error) throw error;

      setLiveData(data || []);
      if (data && data.length > 0) {
        setLastUpdate(new Date());
      }
    } catch (err) {
      console.error('Error loading initial data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load data');
    }
  };

  const formatMetrics = (metrics: Record<string, any>) => {
    return Object.entries(metrics).map(([key, value]) => (
      <div key={key} className="text-xs">
        <span className="font-medium">{key}:</span> {String(value)}
      </div>
    ));
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  if (!supabaseConfigured) {
    return (
      <Card className="w-full">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            <CardTitle>Live Data Stream</CardTitle>
            <Badge variant="secondary" className="ml-2">
              🔴 Not Configured
            </Badge>
          </div>
          <CardDescription>
            Real-time data ingestion from external systems
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive" className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Supabase environment variables are not configured. Please check your project settings and ensure VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are set.
            </AlertDescription>
          </Alert>
          <div className="text-center py-8 text-muted-foreground">
            <Activity className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>Live data stream requires Supabase configuration</p>
            <p className="text-xs mt-1">
              Please configure your Supabase environment variables
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            <CardTitle>Live Data Stream</CardTitle>
            <Badge variant={isConnected ? "default" : "secondary"} className="ml-2">
              {isConnected ? "🟢 Live" : "🔴 Offline"}
            </Badge>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={loadInitialData}
            className="flex items-center gap-1"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>
        <CardDescription>
          Real-time data ingestion from external systems
          {lastUpdate && (
            <span className="block text-xs text-muted-foreground mt-1">
              Last update: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {liveData.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Activity className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>No live data received yet</p>
            <p className="text-xs mt-1">
              Send POST requests to your API endpoint to see data here
            </p>
          </div>
        ) : (
          <div className="rounded-md border overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Time</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Metrics</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {liveData.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell className="font-mono text-xs">
                      {formatTimestamp(entry.timestamp)}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{entry.source}</Badge>
                    </TableCell>
                    <TableCell className="max-w-xs">
                      <div className="space-y-1">
                        {formatMetrics(entry.metrics)}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="default" className="text-xs">
                        Received
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default LiveDataStream;
