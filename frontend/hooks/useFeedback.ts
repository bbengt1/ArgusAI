/**
 * Story P4-5.1: Feedback Collection UI
 *
 * Custom hooks for managing event feedback using TanStack Query mutations.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, ApiError } from '@/lib/api-client';
import type { IEventFeedback } from '@/types/event';

interface SubmitFeedbackParams {
  eventId: string;
  rating: 'helpful' | 'not_helpful';
  correction?: string;
}

interface UpdateFeedbackParams {
  eventId: string;
  rating?: 'helpful' | 'not_helpful';
  correction?: string;
}

/**
 * Hook for submitting feedback on an event
 *
 * @example
 * const { mutate: submitFeedback, isPending } = useSubmitFeedback();
 * submitFeedback({ eventId: '123', rating: 'helpful' });
 */
export function useSubmitFeedback() {
  const queryClient = useQueryClient();

  return useMutation<IEventFeedback, ApiError, SubmitFeedbackParams>({
    mutationFn: async ({ eventId, rating, correction }) => {
      return apiClient.events.submitFeedback(eventId, { rating, correction });
    },
    onSuccess: (data, variables) => {
      // Invalidate event queries to refresh feedback data
      queryClient.invalidateQueries({ queryKey: ['events'] });
      queryClient.invalidateQueries({ queryKey: ['event', variables.eventId] });
    },
  });
}

/**
 * Hook for updating existing feedback on an event
 *
 * @example
 * const { mutate: updateFeedback, isPending } = useUpdateFeedback();
 * updateFeedback({ eventId: '123', rating: 'not_helpful', correction: 'Wrong description' });
 */
export function useUpdateFeedback() {
  const queryClient = useQueryClient();

  return useMutation<IEventFeedback, ApiError, UpdateFeedbackParams>({
    mutationFn: async ({ eventId, rating, correction }) => {
      return apiClient.events.updateFeedback(eventId, { rating, correction });
    },
    onSuccess: (data, variables) => {
      // Invalidate event queries to refresh feedback data
      queryClient.invalidateQueries({ queryKey: ['events'] });
      queryClient.invalidateQueries({ queryKey: ['event', variables.eventId] });
    },
  });
}

/**
 * Hook for deleting feedback from an event
 *
 * @example
 * const { mutate: deleteFeedback, isPending } = useDeleteFeedback();
 * deleteFeedback('123');
 */
export function useDeleteFeedback() {
  const queryClient = useQueryClient();

  return useMutation<void, ApiError, string>({
    mutationFn: async (eventId) => {
      return apiClient.events.deleteFeedback(eventId);
    },
    onSuccess: (_, eventId) => {
      // Invalidate event queries to refresh feedback data
      queryClient.invalidateQueries({ queryKey: ['events'] });
      queryClient.invalidateQueries({ queryKey: ['event', eventId] });
    },
  });
}
