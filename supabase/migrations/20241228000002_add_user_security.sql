
-- Add user_id column to live_data_stream table
ALTER TABLE public.live_data_stream 
ADD COLUMN user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

-- Create user_api_keys table for secure API key management
CREATE TABLE IF NOT EXISTS public.user_api_keys (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    key_hash TEXT NOT NULL UNIQUE,
    key_prefix TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_api_keys_user_id ON public.user_api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_user_api_keys_hash ON public.user_api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_live_data_stream_user_id ON public.live_data_stream(user_id);

-- Enable RLS on the new table
ALTER TABLE public.user_api_keys ENABLE ROW LEVEL SECURITY;

-- Drop the overly permissive policies
DROP POLICY IF EXISTS "Allow read access to live data stream" ON public.live_data_stream;
DROP POLICY IF EXISTS "Allow insert via service role" ON public.live_data_stream;

-- Create secure user-scoped policies for live_data_stream
CREATE POLICY "Users can view their own live data" 
ON public.live_data_stream 
FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own live data" 
ON public.live_data_stream 
FOR INSERT 
WITH CHECK (auth.uid() = user_id);

-- Create policies for user_api_keys
CREATE POLICY "Users can view their own API keys" 
ON public.user_api_keys 
FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own API keys" 
ON public.user_api_keys 
FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own API keys" 
ON public.user_api_keys 
FOR UPDATE 
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own API keys" 
ON public.user_api_keys 
FOR DELETE 
USING (auth.uid() = user_id);
