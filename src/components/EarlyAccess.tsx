import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Alert, AlertDescription } from '@/components/ui/alert';
import HoneypotField from '@/components/HoneypotField';
import { INTEREST_OPTIONS } from '@/lib/dataSources';
import { submitLead } from '@/lib/leadCapture';
import { reservationLink } from '@/lib/reservation';

const InterestForm = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [company, setCompany] = useState('');
  const [interests, setInterests] = useState<string[]>([]);
  const [honeypot, setHoneypot] = useState('');
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggle = (label: string, checked: boolean) =>
    setInterests((current) =>
      checked ? [...current, label] : current.filter((item) => item !== label),
    );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSending(true);
    setError(null);

    const result = await submitLead(
      'interest',
      { name, email, company, interests: interests.join(', ') },
      honeypot,
    );
    setSending(false);

    if (!result.ok) {
      // Keep what the visitor entered so they can retry.
      setError(result.message);
      return;
    }

    setSent(true);
  };

  if (sent) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>You're on the list</CardTitle>
          <CardDescription>We'll email you when the things you picked are ready.</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Join the Interest List</CardTitle>
        <CardDescription>
          Tell us what you are waiting for and we'll email you when it is ready. No payment needed.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <HoneypotField value={honeypot} onChange={setHoneypot} />

          <div className="space-y-2">
            <Label htmlFor="interest-name">Full Name</Label>
            <Input id="interest-name" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="interest-email">Work Email</Label>
            <Input
              id="interest-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="interest-company">Company (optional)</Label>
            <Input id="interest-company" value={company} onChange={(e) => setCompany(e.target.value)} />
          </div>

          <fieldset className="space-y-2">
            <legend className="text-sm font-medium mb-2">I'm interested in</legend>
            {INTEREST_OPTIONS.map((option) => (
              <div key={option.id} className="flex items-center gap-2">
                <Checkbox
                  id={`interest-${option.id}`}
                  checked={interests.includes(option.label)}
                  onCheckedChange={(checked) => toggle(option.label, checked === true)}
                />
                <Label htmlFor={`interest-${option.id}`} className="font-normal">
                  {option.label}
                </Label>
              </div>
            ))}
          </fieldset>

          {error && (
            <Alert variant="destructive" role="alert">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Button
            type="submit"
            className="w-full bg-savvy-gold hover:bg-savvy-gold/90 text-white"
            disabled={sending}
          >
            {sending ? 'Sending...' : 'Join the List'}
          </Button>
          <p className="text-xs text-muted-foreground text-center">
            By joining, you agree to be emailed about SAINT. Ask us to remove you at any time.
          </p>
        </form>
      </CardContent>
    </Card>
  );
};

/** Hidden until the owner sets VITE_STRIPE_PAYMENT_LINK to a Stripe Payment Link. */
const ReserveSpot = () => {
  const link = reservationLink();
  if (!link) return null;

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Reserve Your Spot</CardTitle>
        <CardDescription>
          Pay a refundable deposit to hold a place in line for early access to the self-serve
          version of SAINT.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <ul className="text-sm space-y-2 text-muted-foreground">
          <li>We refund the deposit in full if you ask before your access begins.</li>
          <li>The amount is shown on the secure payment page before you pay.</li>
          <li>Stripe handles the payment. We never see your card details.</li>
        </ul>
        <Button asChild size="lg" className="w-full bg-savvy-gold hover:bg-savvy-gold/90 text-white">
          <a href={link} target="_blank" rel="noopener noreferrer">
            Reserve Your Spot
          </a>
        </Button>
      </CardContent>
    </Card>
  );
};

const EarlyAccess = () => {
  const showReserve = reservationLink() !== null;

  return (
    <section className="py-16 bg-savvy-slate/5" id="early-access">
      <div className="container px-4 md:px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold">Get Early Access</h2>
          <p className="text-muted-foreground mt-3 max-w-2xl mx-auto">
            Hear first when new data sources and the self-serve app arrive.
            {showReserve && ' Want a guaranteed place? Reserve one with a refundable deposit.'}
          </p>
        </div>

        <div
          className={`grid grid-cols-1 gap-6 mx-auto ${showReserve ? 'md:grid-cols-2 max-w-4xl' : 'max-w-xl'}`}
        >
          <InterestForm />
          <ReserveSpot />
        </div>
      </div>
    </section>
  );
};

export default EarlyAccess;
