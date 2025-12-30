/**
 * useSummaries Hooks Tests
 *
 * Tests for activity summary hooks: useRecentSummaries, useGenerateSummary, useSummaryList
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useRecentSummaries, useGenerateSummary, useSummaryList } from '@/hooks/useSummaries';
import { apiClient } from '@/lib/api-client';
import React from 'react';

// Mock the API client
vi.mock('@/lib/api-client', () => ({
  apiClient: {
    summaries: {
      recent: vi.fn(),
      generate: vi.fn(),
      list: vi.fn(),
    },
  },
}));

describe('useSummaries hooks', () => {
  let queryClient: QueryClient;

  const mockRecentSummaries = {
    today: {
      summary_id: 'sum-today',
      summary_type: 'daily',
      period_label: 'Today',
      narrative: 'Quiet day with minimal activity',
      event_count: 5,
      key_observations: ['Person at front door', 'Vehicle in driveway'],
      start_time: '2024-06-01T00:00:00Z',
      end_time: '2024-06-01T23:59:59Z',
    },
    yesterday: {
      summary_id: 'sum-yesterday',
      summary_type: 'daily',
      period_label: 'Yesterday',
      narrative: 'Busy day with many deliveries',
      event_count: 25,
      key_observations: ['Multiple package deliveries', 'Visitors in afternoon'],
      start_time: '2024-05-31T00:00:00Z',
      end_time: '2024-05-31T23:59:59Z',
    },
  };

  const mockGenerateResponse = {
    summary: {
      id: 'sum-new',
      summary_type: 'custom',
      narrative: 'Summary for the last 3 hours',
      event_count: 10,
      key_observations: ['Activity detected'],
      start_time: '2024-06-01T09:00:00Z',
      end_time: '2024-06-01T12:00:00Z',
      created_at: '2024-06-01T12:00:00Z',
    },
    event_count: 10,
    success: true,
  };

  const mockSummaryList = {
    summaries: [
      {
        id: 'sum-1',
        summary_type: 'daily',
        narrative: 'Day 1 summary',
        event_count: 15,
        created_at: '2024-06-01T00:00:00Z',
      },
      {
        id: 'sum-2',
        summary_type: 'daily',
        narrative: 'Day 2 summary',
        event_count: 20,
        created_at: '2024-05-31T00:00:00Z',
      },
    ],
    total: 2,
    limit: 20,
    offset: 0,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          gcTime: 0,
        },
        mutations: {
          retry: false,
        },
      },
    });
  });

  const wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);

  describe('useRecentSummaries', () => {
    it('fetches recent summaries successfully', async () => {
      (apiClient.summaries.recent as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockRecentSummaries);

      const { result } = renderHook(() => useRecentSummaries(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toEqual(mockRecentSummaries);
      expect(apiClient.summaries.recent).toHaveBeenCalledTimes(1);
    });

    it('handles fetch error', async () => {
      const error = new Error('Network error');
      (apiClient.summaries.recent as ReturnType<typeof vi.fn>).mockRejectedValueOnce(error);

      const { result } = renderHook(() => useRecentSummaries(), { wrapper });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBeTruthy();
    });

    it('returns today and yesterday summaries', async () => {
      (apiClient.summaries.recent as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockRecentSummaries);

      const { result } = renderHook(() => useRecentSummaries(), { wrapper });

      await waitFor(() => {
        expect(result.current.data).toBeDefined();
      });

      expect(result.current.data?.today).toBeDefined();
      expect(result.current.data?.yesterday).toBeDefined();
      expect(result.current.data?.today.period_label).toBe('Today');
      expect(result.current.data?.yesterday.period_label).toBe('Yesterday');
    });
  });

  describe('useGenerateSummary', () => {
    it('generates summary for hours_back', async () => {
      (apiClient.summaries.generate as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockGenerateResponse);

      const { result } = renderHook(() => useGenerateSummary(), { wrapper });

      await act(async () => {
        await result.current.mutateAsync({ hours_back: 3 });
      });

      expect(apiClient.summaries.generate).toHaveBeenCalledWith({ hours_back: 3 });
    });

    it('generates summary for time range', async () => {
      (apiClient.summaries.generate as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockGenerateResponse);

      const { result } = renderHook(() => useGenerateSummary(), { wrapper });

      const params = {
        start_time: '2024-06-01T00:00:00Z',
        end_time: '2024-06-01T12:00:00Z',
      };

      await act(async () => {
        await result.current.mutateAsync(params);
      });

      expect(apiClient.summaries.generate).toHaveBeenCalledWith(params);
    });

    it('handles generation error', async () => {
      const error = new Error('Generation failed');
      (apiClient.summaries.generate as ReturnType<typeof vi.fn>).mockRejectedValueOnce(error);

      const { result } = renderHook(() => useGenerateSummary(), { wrapper });

      await expect(result.current.mutateAsync({ hours_back: 1 })).rejects.toThrow('Generation failed');
    });

    it('invalidates summaries cache on success', async () => {
      (apiClient.summaries.generate as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockGenerateResponse);
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const { result } = renderHook(() => useGenerateSummary(), { wrapper });

      await act(async () => {
        await result.current.mutateAsync({ hours_back: 3 });
      });

      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['summaries'] });
    });

    it('returns generated summary data', async () => {
      (apiClient.summaries.generate as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockGenerateResponse);

      const { result } = renderHook(() => useGenerateSummary(), { wrapper });

      let response;
      await act(async () => {
        response = await result.current.mutateAsync({ hours_back: 3 });
      });

      expect(response).toEqual(mockGenerateResponse);
      expect(response.summary.event_count).toBe(10);
    });
  });

  describe('useSummaryList', () => {
    it('fetches summary list with default pagination', async () => {
      (apiClient.summaries.list as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockSummaryList);

      const { result } = renderHook(() => useSummaryList(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toEqual(mockSummaryList);
      expect(apiClient.summaries.list).toHaveBeenCalledWith(20, 0);
    });

    it('fetches summary list with custom pagination', async () => {
      (apiClient.summaries.list as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockSummaryList);

      const { result } = renderHook(() => useSummaryList(10, 5), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(apiClient.summaries.list).toHaveBeenCalledWith(10, 5);
    });

    it('handles fetch error', async () => {
      const error = new Error('List failed');
      (apiClient.summaries.list as ReturnType<typeof vi.fn>).mockRejectedValueOnce(error);

      const { result } = renderHook(() => useSummaryList(), { wrapper });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });
    });

    it('returns summaries array with metadata', async () => {
      (apiClient.summaries.list as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockSummaryList);

      const { result } = renderHook(() => useSummaryList(), { wrapper });

      await waitFor(() => {
        expect(result.current.data).toBeDefined();
      });

      expect(result.current.data?.summaries).toHaveLength(2);
      expect(result.current.data?.total).toBe(2);
    });
  });
});
