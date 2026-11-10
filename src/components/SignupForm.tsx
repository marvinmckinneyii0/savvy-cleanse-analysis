
import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import HoneypotField from '@/components/HoneypotField';
import { submitLead } from '@/lib/leadCapture';

const SignupForm = () => {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [company, setCompany] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [honeypot, setHoneypot] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const result = await submitLead('signup', { name, email, company }, honeypot);
    setLoading(false);

    if (!result.ok) {
      // Keep what the visitor typed so they can retry.
      setError(result.message);
      return;
    }

    setSuccess(true);
    setEmail('');
    setName('');
    setCompany('');
  };

  if (success) {
    return (
      <Card id="signup-form" className="w-full max-w-md mx-auto">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold text-savvy-gold">
            Thank you!
          </CardTitle>
          <CardDescription>
            We'll reply by email with how to send your CSV.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card id="signup-form" className="w-full max-w-md mx-auto">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl font-bold">
          Request a Data-Quality Report
        </CardTitle>
        <CardDescription>
          Leave your details and we'll reply by email with how to send your CSV.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <HoneypotField value={honeypot} onChange={setHoneypot} />
          <div className="space-y-2">
            <Label htmlFor="name">Full Name</Label>
            <Input
              id="name"
              type="text"
              placeholder="Enter your full name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="email">Work Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="Enter your work email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="company">Company</Label>
            <Input
              id="company"
              type="text"
              placeholder="Enter your company name"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              required
            />
          </div>

          {error && (
            <Alert variant="destructive" role="alert">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Button 
            type="submit" 
            className="w-full bg-savvy-gold hover:bg-savvy-gold/90 text-white" 
            disabled={loading}
          >
            {loading ? 'Sending...' : 'Request Report'}
          </Button>
        </form>
        
        <p className="text-xs text-muted-foreground text-center mt-4">
          By submitting, you agree to be contacted about your request.
        </p>
      </CardContent>
    </Card>
  );
};

export default SignupForm;
