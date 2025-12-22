/**
 * Story P4-5.1: Feedback Collection UI
 * Story P9-3.3: Package False Positive Feedback
 *
 * FeedbackButtons component - allows users to provide quick feedback on AI event descriptions
 * using thumbs up/down buttons with optional correction text input.
 * For package detections, includes a "Not a package" button.
 */

'use client';

import { useState, memo, useCallback } from 'react';
import { ThumbsUp, ThumbsDown, Loader2, X, Package } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { useSubmitFeedback, useUpdateFeedback } from '@/hooks/useFeedback';
import type { IEventFeedback } from '@/types/event';
import { cn } from '@/lib/utils';

interface FeedbackButtonsProps {
  /** Event UUID to submit feedback for */
  eventId: string;
  /** Existing feedback if any (for showing selected state) */
  existingFeedback?: IEventFeedback | null;
  /** Callback when feedback changes */
  onFeedbackChange?: (feedback: IEventFeedback) => void;
  /** Additional class names */
  className?: string;
  /** Story P9-3.3: Smart detection type for showing correction buttons */
  smartDetectionType?: string | null;
}

const CORRECTION_MAX_LENGTH = 500;

export const FeedbackButtons = memo(function FeedbackButtons({
  eventId,
  existingFeedback,
  onFeedbackChange,
  className,
  smartDetectionType,
}: FeedbackButtonsProps) {
  const [showCorrection, setShowCorrection] = useState(false);
  const [correction, setCorrection] = useState('');
  const [localFeedback, setLocalFeedback] = useState<IEventFeedback | null>(existingFeedback ?? null);

  const { mutate: submitFeedback, isPending: isSubmitting } = useSubmitFeedback();
  const { mutate: updateFeedback, isPending: isUpdating } = useUpdateFeedback();

  const isPending = isSubmitting || isUpdating;

  // Get current rating (from local state or prop)
  const currentRating = localFeedback?.rating ?? existingFeedback?.rating;
  // Story P9-3.3: Get current correction type
  const currentCorrectionType = localFeedback?.correction_type ?? existingFeedback?.correction_type;
  const isPackageEvent = smartDetectionType === 'package';
  const isMarkedNotPackage = currentCorrectionType === 'not_package';

  const handleFeedback = useCallback((
    rating: 'helpful' | 'not_helpful',
    correctionText?: string,
    correctionType?: 'not_package'
  ) => {
    const mutationFn = currentRating ? updateFeedback : submitFeedback;

    mutationFn(
      {
        eventId,
        rating,
        correction: correctionText || undefined,
        correction_type: correctionType,
      },
      {
        onSuccess: (data) => {
          // Extract feedback from the returned event
          if (data.feedback) {
            setLocalFeedback(data.feedback);
            onFeedbackChange?.(data.feedback);
          }
          setShowCorrection(false);
          setCorrection('');
          // Story P9-3.3: Different toast for package false positive
          if (correctionType === 'not_package') {
            toast.success('Feedback recorded', {
              description: 'Thanks! This helps improve package detection accuracy.',
            });
          } else {
            toast.success('Feedback submitted', {
              description: rating === 'helpful' ? 'Thanks for the feedback!' : 'Thanks! Your correction helps improve accuracy.',
            });
          }
        },
        onError: (error) => {
          toast.error('Failed to submit feedback', {
            description: error.message || 'Please try again.',
          });
        },
      }
    );
  }, [eventId, currentRating, submitFeedback, updateFeedback, onFeedbackChange]);

  const handleThumbsUp = useCallback((e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent EventCard click
    if (isPending) return;
    handleFeedback('helpful');
  }, [handleFeedback, isPending]);

  const handleThumbsDown = useCallback((e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent EventCard click
    if (isPending) return;
    setShowCorrection(true);
  }, [isPending]);

  // Story P9-3.3: Handle "Not a package" click
  const handleNotPackage = useCallback((e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent EventCard click
    if (isPending || isMarkedNotPackage) return;
    handleFeedback('not_helpful', undefined, 'not_package');
  }, [handleFeedback, isPending, isMarkedNotPackage]);

  const handleSubmitCorrection = useCallback((e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent EventCard click
    if (isPending) return;
    handleFeedback('not_helpful', correction);
  }, [handleFeedback, correction, isPending]);

  const handleSkipCorrection = useCallback((e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent EventCard click
    if (isPending) return;
    handleFeedback('not_helpful');
  }, [handleFeedback, isPending]);

  const handleCancelCorrection = useCallback((e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent EventCard click
    setShowCorrection(false);
    setCorrection('');
  }, []);

  const handleCorrectionChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    if (value.length <= CORRECTION_MAX_LENGTH) {
      setCorrection(value);
    }
  }, []);

  // Prevent clicks from bubbling to EventCard
  const handleContainerClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
  }, []);

  return (
    <div className={cn("flex flex-col gap-2", className)} onClick={handleContainerClick}>
      <div className="flex items-center gap-1">
        {/* Thumbs Up Button */}
        <Button
          variant={currentRating === 'helpful' ? 'default' : 'ghost'}
          size="sm"
          onClick={handleThumbsUp}
          disabled={isPending}
          aria-label={currentRating === 'helpful' ? 'Marked as helpful' : 'Mark as helpful'}
          aria-pressed={currentRating === 'helpful'}
          className={cn(
            "h-8 w-8 p-0",
            currentRating === 'helpful' && "bg-green-600 hover:bg-green-700 text-white"
          )}
        >
          {isPending && !showCorrection ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <ThumbsUp className={cn(
              "h-4 w-4",
              currentRating === 'helpful' && "fill-current"
            )} />
          )}
        </Button>

        {/* Thumbs Down Button */}
        <Button
          variant={currentRating === 'not_helpful' ? 'default' : 'ghost'}
          size="sm"
          onClick={handleThumbsDown}
          disabled={isPending}
          aria-label={currentRating === 'not_helpful' ? 'Marked as not helpful' : 'Mark as not helpful'}
          aria-pressed={currentRating === 'not_helpful'}
          className={cn(
            "h-8 w-8 p-0",
            currentRating === 'not_helpful' && "bg-red-600 hover:bg-red-700 text-white"
          )}
        >
          <ThumbsDown className={cn(
            "h-4 w-4",
            currentRating === 'not_helpful' && "fill-current"
          )} />
        </Button>

        {/* Story P9-3.3: "Not a package" Button for package events */}
        {isPackageEvent && (
          <Button
            variant={isMarkedNotPackage ? 'default' : 'outline'}
            size="sm"
            onClick={handleNotPackage}
            disabled={isPending || isMarkedNotPackage}
            aria-label={isMarkedNotPackage ? 'Marked as not a package' : 'Not a package'}
            aria-pressed={isMarkedNotPackage}
            className={cn(
              "h-8 px-2 text-xs gap-1",
              isMarkedNotPackage && "bg-orange-600 hover:bg-orange-600 text-white cursor-default"
            )}
          >
            <Package className="h-3 w-3" />
            <X className="h-3 w-3 -ml-1" />
            {isMarkedNotPackage ? 'Not a package' : 'Not a package'}
          </Button>
        )}
      </div>

      {/* Correction Input (shows on thumbs down) */}
      {showCorrection && (
        <div className="flex flex-col gap-2 p-3 bg-muted rounded-lg border animate-in fade-in slide-in-from-top-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">What should it say? (optional)</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCancelCorrection}
              className="h-6 w-6 p-0"
              aria-label="Cancel correction"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          <Textarea
            value={correction}
            onChange={handleCorrectionChange}
            placeholder="Enter the correct description..."
            className="min-h-[80px] text-sm resize-none"
            maxLength={CORRECTION_MAX_LENGTH}
            aria-label="Correction text"
          />
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">
              {correction.length}/{CORRECTION_MAX_LENGTH}
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleSkipCorrection}
                disabled={isPending}
              >
                Skip
              </Button>
              <Button
                size="sm"
                onClick={handleSubmitCorrection}
                disabled={isPending}
              >
                {isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  'Submit'
                )}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
});
