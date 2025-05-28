
-- Create the live_data_stream table
CREATE TABLE IF NOT EXISTS public.live_data_stream (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    source TEXT NOT NULL,
    metrics JSONB NOT NULL,
    raw_data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_live_data_stream_timestamp ON public.live_data_stream(timestamp);
CREATE INDEX IF NOT EXISTS idx_live_data_stream_source ON public.live_data_stream(source);
CREATE INDEX IF NOT EXISTS idx_live_data_stream_created_at ON public.live_data_stream(created_at);

-- Enable real-time subscriptions
ALTER PUBLICATION supabase_realtime ADD TABLE public.live_data_stream;

-- Set up Row Level Security (RLS)
ALTER TABLE public.live_data_stream ENABLE ROW LEVEL SECURITY;

-- Create a policy that allows read access to all authenticated users
CREATE POLICY "Allow read access to live data stream" 
ON public.live_data_stream 
FOR SELECT 
USING (true);

-- Create a policy that allows insert access (for the edge function using service role key)
CREATE POLICY "Allow insert via service role" 
ON public.live_data_stream 
FOR INSERT 
WITH CHECK (true);
