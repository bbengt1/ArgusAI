/**
 * Story P4-5.3: Accuracy Dashboard
 *
 * Custom hook for fetching feedback statistics using TanStack Query.
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type { IFeedbackStats } from '@/types/event';

interface FeedbackStatsParams {
  camera_id?: string;
  start_date?: string;
  end_date?: string;
}

/**
 * Hook for fetching aggregate feedback statistics
 *
 * @param params Optional filters: camera_id, start_date, end_date
 * @returns Query result with feedback stats data, loading state, and error
 *
 * @example
 * const { data, isLoading, error } = useFeedbackStats({
 *   camera_id: 'abc123',
 *   start_date: '2025-12-01',
 *   end_date: '2025-12-12'
 * });
 */
export function useFeedbackStats(params?: FeedbackStatsParams) {
  return useQuery<IFeedbackStats>({
    queryKey: ['feedback-stats', params?.camera_id, params?.start_date, params?.end_date],
    queryFn: () => apiClient.feedback.getStats(params),
    staleTime: 60 * 1000, // Consider data fresh for 1 minute
    refetchOnWindowFocus: false,
  });
}
