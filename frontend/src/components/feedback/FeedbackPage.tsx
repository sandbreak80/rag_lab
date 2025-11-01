import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '../../services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { Label } from '../ui/label';
import { Star, CheckCircle } from 'lucide-react';

const FEEDBACK_CATEGORIES = [
  'Application usability',
  'Lab content quality',
  'RAG system features',
  'AI/ML concepts clarity',
  'Lab delivery method',
];

export function FeedbackPage() {
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [categories, setCategories] = useState<string[]>([]);
  const [comments, setComments] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const submitMutation = useMutation({
    mutationFn: (data: { rating: number; categories: string[]; comments: string }) =>
      api.submitFeedback(data),
    onSuccess: () => {
      setSubmitted(true);
      // Reset form after 3 seconds
      setTimeout(() => {
        setRating(0);
        setCategories([]);
        setComments('');
        setSubmitted(false);
      }, 3000);
    },
  });

  const toggleCategory = (category: string) => {
    if (categories.includes(category)) {
      setCategories(categories.filter((c) => c !== category));
    } else {
      setCategories([...categories, category]);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (rating === 0) {
      alert('Please provide a rating');
      return;
    }
    submitMutation.mutate({ rating, categories, comments });
  };

  if (submitted) {
    return (
      <div className="space-y-6">
        <Card className="max-w-2xl mx-auto">
          <CardContent className="p-12 text-center">
            <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">Thank You!</h2>
            <p className="text-muted-foreground">
              Your feedback has been submitted successfully.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">💭 Your Feedback</h1>
        <p className="text-muted-foreground">
          Help us improve this RAG lab! Your input is valuable.
        </p>
      </div>

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Share Your Experience</CardTitle>
          <CardDescription>
            Tell us what worked well and what could be improved
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Rating */}
            <div className="space-y-2">
              <Label>Overall Rating *</Label>
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setRating(star)}
                    onMouseEnter={() => setHoverRating(star)}
                    onMouseLeave={() => setHoverRating(0)}
                    className="transition-transform hover:scale-110"
                  >
                    <Star
                      className={`h-8 w-8 ${
                        star <= (hoverRating || rating)
                          ? 'fill-yellow-500 text-yellow-500'
                          : 'text-muted-foreground'
                      }`}
                    />
                  </button>
                ))}
              </div>
              <p className="text-xs text-muted-foreground">
                {rating === 0 && 'Select a rating'}
                {rating === 1 && 'Poor'}
                {rating === 2 && 'Fair'}
                {rating === 3 && 'Good'}
                {rating === 4 && 'Very Good'}
                {rating === 5 && 'Excellent'}
              </p>
            </div>

            {/* Categories */}
            <div className="space-y-2">
              <Label>What aspects stood out?</Label>
              <div className="flex flex-wrap gap-2">
                {FEEDBACK_CATEGORIES.map((category) => (
                  <button
                    key={category}
                    type="button"
                    onClick={() => toggleCategory(category)}
                    className={`px-3 py-1.5 rounded-full text-sm transition-colors ${
                      categories.includes(category)
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-secondary/20 hover:bg-secondary/30'
                    }`}
                  >
                    {category}
                  </button>
                ))}
              </div>
            </div>

            {/* Comments */}
            <div className="space-y-2">
              <Label htmlFor="comments">Additional Comments</Label>
              <Textarea
                id="comments"
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                placeholder="Share your thoughts, suggestions, or concerns..."
                className="min-h-[120px]"
              />
            </div>

            {/* Submit */}
            <Button
              type="submit"
              className="w-full"
              disabled={submitMutation.isPending || rating === 0}
            >
              {submitMutation.isPending ? 'Submitting...' : 'Submit Feedback'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
