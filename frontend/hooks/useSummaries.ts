/**
 * TanStack Query hooks for Activity Summaries (Story P4-4.4, P4-4.5)
 *
 * Provides hooks for fetching recent activity summaries and generating on-demand summaries.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  apiClient,
  RecentSummariesResponse,
  RecentSummaryItem,
  SummaryGenerateRequest,
  SummaryGenerateResponse,
  SummaryStats,
  SummaryListResponse,
} from '@/lib/api-client';

// Re-export types for convenience
export type {
  RecentSummariesResponse,
  RecentSummaryItem,
  SummaryGenerateRequest,
  SummaryGenerateResponse,
  SummaryStats,
  SummaryListResponse,
};

/**
 * Hook to fetch recent summaries (today and yesterday) for dashboard display.
 *
 * AC11: SummaryCard refreshes data every 5 minutes using TanStack Query
 *
 * @returns TanStack Query result with recent summaries
 */
export function useRecentSummaries() {
  return useQuery({
    queryKey: ['summaries', 'recent'],
    queryFn: async (): Promise<RecentSummariesResponse> => {
      return apiClient.summaries.recent();
    },
    refetchInterval: 5 * 60 * 1000, // 5 minutes (AC11)
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Hook to generate an on-demand summary (Story P4-4.5)
 *
 * Uses useMutation for POST request with automatic cache invalidation.
 *
 * @returns TanStack Query mutation result for generating summaries
 *
 * Usage:
 * ```tsx
 * const generateMutation = useGenerateSummary();
 *
 * // Generate summary for last 3 hours
 * generateMutation.mutate({ hours_back: 3 });
 *
 * // Generate summary for specific time range
 * generateMutation.mutate({
 *   start_time: '2025-01-01T00:00:00Z',
 *   end_time: '2025-01-01T23:59:59Z'
 * });
 * ```
 */
export function useGenerateSummary() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: SummaryGenerateRequest): Promise<SummaryGenerateResponse> => {
      return apiClient.summaries.generate(params);
    },
    onSuccess: () => {
      // Invalidate summaries queries to refresh the list
      queryClient.invalidateQueries({ queryKey: ['summaries'] });
    },
  });
}

/**
 * Hook to fetch list of all summaries with pagination (Story P4-4.5)
 *
 * @param limit Maximum number of summaries to return
 * @param offset Pagination offset
 * @returns TanStack Query result with summary list
 */
export function useSummaryList(limit = 20, offset = 0) {
  return useQuery({
    queryKey: ['summaries', 'list', limit, offset],
    queryFn: async (): Promise<SummaryListResponse> => {
      return apiClient.summaries.list(limit, offset);
    },
    staleTime: 60 * 1000, // 1 minute
  });
}
