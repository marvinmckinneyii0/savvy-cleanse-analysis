
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { crypto } from "https://deno.land/std@0.168.0/crypto/mod.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-api-key',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}

// Rate limiting store (in production, use Redis or similar)
const rateLimitStore = new Map<string, { count: number; resetTime: number }>();

const isValidApiKeyFormat = (key: string): boolean => {
  return /^sk_[a-zA-Z0-9]{32}$/.test(key);
};

const hashApiKey = async (key: string): Promise<string> => {
  const encoder = new TextEncoder();
  const data = encoder.encode(key);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
};

const checkRateLimit = (keyHash: string): boolean => {
  const now = Date.now();
  const windowMs = 60 * 1000; // 1 minute
  const maxRequests = 100; // 100 requests per minute per API key

  const current = rateLimitStore.get(keyHash);
  
  if (!current || now > current.resetTime) {
    rateLimitStore.set(keyHash, { count: 1, resetTime: now + windowMs });
    return true;
  }
  
  if (current.count >= maxRequests) {
    return false;
  }
  
  current.count++;
  return true;
};

const validatePayload = (body: any): { valid: boolean; errors: string[] } => {
  const errors: string[] = [];
  
  // Check required fields
  if (!body.timestamp) errors.push('timestamp is required');
  if (!body.source) errors.push('source is required');
  if (!body.metrics) errors.push('metrics is required');
  
  // Validate timestamp format
  if (body.timestamp && isNaN(new Date(body.timestamp).getTime())) {
    errors.push('Invalid timestamp format. Use ISO 8601 format.');
  }
  
  // Validate source field (prevent injection)
  if (body.source && (typeof body.source !== 'string' || body.source.length > 100)) {
    errors.push('source must be a string with maximum 100 characters');
  }
  
  // Validate metrics object
  if (body.metrics && typeof body.metrics !== 'object') {
    errors.push('metrics must be an object');
  }
  
  // Check payload size (approximate)
  const payloadSize = JSON.stringify(body).length;
  if (payloadSize > 100000) { // 100KB limit
    errors.push('Payload too large. Maximum size is 100KB');
  }
  
  return { valid: errors.length === 0, errors };
};

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Validate method
    if (req.method !== 'POST') {
      return new Response(
        JSON.stringify({ error: 'Method not allowed' }),
        { 
          status: 405, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Validate API key format
    const apiKey = req.headers.get('x-api-key')
    if (!apiKey || !isValidApiKeyFormat(apiKey)) {
      return new Response(
        JSON.stringify({ error: 'Invalid API key format' }),
        { 
          status: 401, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Hash the API key for lookup
    const keyHash = await hashApiKey(apiKey);

    // Check rate limit
    if (!checkRateLimit(keyHash)) {
      return new Response(
        JSON.stringify({ error: 'Rate limit exceeded' }),
        { 
          status: 429, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Initialize Supabase client
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Verify API key and get user_id
    const { data: apiKeyData, error: keyError } = await supabase
      .from('user_api_keys')
      .select('user_id, is_active')
      .eq('key_hash', keyHash)
      .eq('is_active', true)
      .single();

    if (keyError || !apiKeyData) {
      return new Response(
        JSON.stringify({ error: 'Invalid API key' }),
        { 
          status: 401, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Update last_used_at
    await supabase
      .from('user_api_keys')
      .update({ last_used_at: new Date().toISOString() })
      .eq('key_hash', keyHash);

    // Parse and validate request body
    const body = await req.json()
    const validation = validatePayload(body);
    
    if (!validation.valid) {
      return new Response(
        JSON.stringify({ 
          error: 'Invalid payload',
          details: validation.errors
        }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Sanitize source field
    const sanitizedSource = body.source.trim().replace(/[<>]/g, '');

    // Prepare data for insertion with user_id
    const dataToInsert = {
      timestamp: body.timestamp,
      source: sanitizedSource,
      metrics: body.metrics,
      raw_data: body,
      user_id: apiKeyData.user_id
    }

    // Insert data into Supabase
    const { data, error } = await supabase
      .from('live_data_stream')
      .insert([dataToInsert])
      .select()
      .single()

    if (error) {
      console.error('Database error:', error)
      return new Response(
        JSON.stringify({ error: 'Failed to store data' }),
        { 
          status: 500, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Return success response
    return new Response(
      JSON.stringify({ 
        success: true, 
        message: 'Data received and stored successfully',
        id: data.id,
        timestamp: data.created_at
      }),
      { 
        status: 200, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )

  } catch (error) {
    console.error('Request processing error:', error)
    return new Response(
      JSON.stringify({ 
        error: 'Internal server error'
      }),
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})
