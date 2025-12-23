/**
 * Story P9-3.4: Summary Feedback Buttons
 *
 * Custom hooks for managing summary feedback using TanStack Query mutations.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient, ApiError, SummaryFeedbackResponse } from '@/lib/api-client';
import type { ISummaryFeedback } from '@/types/event';

interface SubmitSummaryFeedbackParams {
  summaryId: string;
  rating: 'positive' | 'negative';
  correctionText?: string;
}

/**
 * Hook for fetching feedback for a summary
 *
 * @example
 * const { data: feedback, isLoading } = useSummaryFeedback('123');
 */
export function useSummaryFeedback(summaryId: string) {
  return useQuery<ISummaryFeedback | null, ApiError>({
    queryKey: ['summaryFeedback', summaryId],
    queryFn: async () => {
      try {
        return await apiClient.summaries.getFeedback(summaryId);
      } catch (error) {
        // Return null for 404 (no feedback exists yet)
        if (error instanceof ApiError && error.statusCode === 404) {
          return null;
        }
        // Silently return null for other errors to avoid UI disruption
        return null;
      }
    },
    enabled: !!summaryId,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/**
 * Hook for submitting feedback on a summary
 *
 * @example
 * const { mutate: submitFeedback, isPending } = useSubmitSummaryFeedback();
 * submitFeedback({ summaryId: '123', rating: 'positive' });
 */
export function useSubmitSummaryFeedback() {
  const queryClient = useQueryClient();

  return useMutation<SummaryFeedbackResponse, ApiError, SubmitSummaryFeedbackParams>({
    mutationFn: async ({ summaryId, rating, correctionText }) => {
      return apiClient.summaries.submitFeedback(summaryId, {
        rating,
        correction_text: correctionText ?? null,
      });
    },
    onSuccess: (_data, variables) => {
      // Invalidate feedback query to refresh data
      queryClient.invalidateQueries({ queryKey: ['summaryFeedback', variables.summaryId] });
      queryClient.invalidateQueries({ queryKey: ['summaries'] });
    },
  });
}

/**
 * Hook for updating existing feedback on a summary
 *
 * @example
 * const { mutate: updateFeedback, isPending } = useUpdateSummaryFeedback();
 * updateFeedback({ summaryId: '123', rating: 'negative', correctionText: 'Missed an event' });
 */
export function useUpdateSummaryFeedback() {
  const queryClient = useQueryClient();

  return useMutation<SummaryFeedbackResponse, ApiError, SubmitSummaryFeedbackParams>({
    mutationFn: async ({ summaryId, rating, correctionText }) => {
      return apiClient.summaries.updateFeedback(summaryId, {
        rating,
        correction_text: correctionText ?? null,
      });
    },
    onSuccess: (_data, variables) => {
      // Invalidate feedback query to refresh data
      queryClient.invalidateQueries({ queryKey: ['summaryFeedback', variables.summaryId] });
      queryClient.invalidateQueries({ queryKey: ['summaries'] });
    },
  });
}

/**
 * Hook for deleting feedback from a summary
 *
 * @example
 * const { mutate: deleteFeedback, isPending } = useDeleteSummaryFeedback();
 * deleteFeedback('123');
 */
export function useDeleteSummaryFeedback() {
  const queryClient = useQueryClient();

  return useMutation<void, ApiError, string>({
    mutationFn: async (summaryId) => {
      return apiClient.summaries.deleteFeedback(summaryId);
    },
    onSuccess: (_, summaryId) => {
      // Invalidate feedback query to refresh data
      queryClient.invalidateQueries({ queryKey: ['summaryFeedback', summaryId] });
      queryClient.invalidateQueries({ queryKey: ['summaries'] });
    },
  });
}
