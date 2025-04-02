
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/use-toast';

const Feedback = () => {
  const [feedback, setFeedback] = useState('');
  const [rating, setRating] = useState<number | null>(null);
  const { toast } = useToast();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!feedback.trim()) {
      toast({
        title: "Feedback required",
        description: "Please provide some feedback before submitting.",
        variant: "destructive",
      });
      return;
    }
    
    // In a real app, this would be sent to a backend API
    console.log("Feedback submitted:", { feedback, rating });
    
    toast({
      title: "Thank you for your feedback!",
      description: "Your input helps us improve SavvyClean.",
    });
    
    // Reset the form
    setFeedback('');
    setRating(null);
  };

  return (
    <section className="py-16 bg-background" id="feedback">
      <div className="container px-4 md:px-6">
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold mb-2">We Value Your Feedback</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Help us improve SavvyClean by sharing your experience and suggestions.
          </p>
        </div>
        
        <div className="max-w-md mx-auto">
          <Card>
            <CardHeader>
              <CardTitle>Share Your Thoughts</CardTitle>
              <CardDescription>
                Your feedback helps us build a better product for data analysts like you.
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleSubmit}>
              <CardContent className="space-y-4">
                <div>
                  <div className="mb-2 text-sm font-medium">How would you rate your experience?</div>
                  <div className="flex space-x-2">
                    {[1, 2, 3, 4, 5].map((value) => (
                      <button
                        key={value}
                        type="button"
                        onClick={() => setRating(value)}
                        className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
                          rating === value 
                            ? 'bg-savvy-gold text-white' 
                            : 'bg-muted hover:bg-muted/80'
                        }`}
                      >
                        {value}
                      </button>
                    ))}
                  </div>
                </div>
                
                <div>
                  <label htmlFor="feedback" className="text-sm font-medium block mb-2">
                    Your feedback
                  </label>
                  <Textarea
                    id="feedback"
                    placeholder="Tell us about your experience or suggest improvements..."
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    rows={4}
                    className="resize-none"
                  />
                </div>
              </CardContent>
              <CardFooter>
                <Button 
                  type="submit" 
                  className="w-full bg-savvy-gold hover:bg-savvy-gold/90"
                >
                  Submit Feedback
                </Button>
              </CardFooter>
            </form>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default Feedback;
