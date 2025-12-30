/**
 * useFeedback Hooks Tests
 *
 * Tests for feedback management hooks: useSubmitFeedback, useUpdateFeedback, useDeleteFeedback
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useSubmitFeedback, useUpdateFeedback, useDeleteFeedback } from '@/hooks/useFeedback';
import { apiClient } from '@/lib/api-client';
import React from 'react';

// Mock the API client
vi.mock('@/lib/api-client', () => ({
  apiClient: {
    events: {
      submitFeedback: vi.fn(),
      updateFeedback: vi.fn(),
      deleteFeedback: vi.fn(),
    },
  },
  ApiError: class ApiError extends Error {
    statusCode: number;
    constructor(message: string, statusCode: number) {
      super(message);
      this.statusCode = statusCode;
    }
  },
}));

describe('useFeedback hooks', () => {
  let queryClient: QueryClient;

  const mockEvent = {
    id: 'event-123',
    camera_id: 'cam-1',
    camera_name: 'Front Door',
    timestamp: '2024-06-01T12:00:00Z',
    description: 'Person detected at front door',
    feedback: {
      rating: 'helpful' as const,
      correction: null,
      correction_type: null,
    },
  };

  const mockFeedbackResponse = {
    id: 'feedback-1',
    event_id: 'event-123',
    rating: 'helpful' as const,
    correction: null,
    correction_type: null,
    created_at: '2024-06-01T12:05:00Z',
    updated_at: '2024-06-01T12:05:00Z',
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

  describe('useSubmitFeedback', () => {
    it('submits feedback successfully', async () => {
      (apiClient.events.submitFeedback as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockEvent);

      const { result } = renderHook(() => useSubmitFeedback(), { wrapper });

      await act(async () => {
        await result.current.mutateAsync({
          eventId: 'event-123',
          rating: 'helpful',
        });
      });

      expect(apiClient.events.submitFeedback).toHaveBeenCalledWith('event-123', {
        rating: 'helpful',
        correction: null,
        correction_type: null,
      });
    });

    it('submits feedback with correction', async () => {
      (apiClient.events.submitFeedback as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockEvent);

      const { result } = renderHook(() => useSubmitFeedback(), { wrapper });

      await act(async () => {
        await result.current.mutateAsync({
          eventId: 'event-123',
          rating: 'not_helpful',
          correction: 'This was not a person',
        });
      });

      expect(apiClient.events.submitFeedback).toHaveBeenCalledWith('event-123', {
        rating: 'not_helpful',
        correction: 'This was not a person',
        correction_type: null,
      });
    });

    it('submits feedback with correction_type for package false positive', async () => {
      (apiClient.events.submitFeedback as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockEvent);

      const { result } = renderHook(() => useSubmitFeedback(), { wrapper });

      await act(async () => {
        await result.current.mutateAsync({
          eventId: 'event-123',
          rating: 'not_helpful',
          correction_type: 'not_package',
        });
      });

      expect(apiClient.events.submitFeedback).toHaveBeenCalledWith('event-123', {
        rating: 'not_helpful',
        correction: null,
        correction_type: 'not_package',
      });
    });

    it('handles submission error', async () => {
      const error = new Error('Submission failed');
      (apiClient.events.submitFeedback as ReturnType<typeof vi.fn>).mockRejectedValueOnce(error);

      const { result } = renderHook(() => useSubmitFeedback(), { wrapper });

      await expect(
        result.current.mutateAsync({
          eventId: 'event-123',
          rating: 'helpful',
        })
      ).rejects.toThrow('Submission failed');
    });

    it('invalidates event queries on success', async () => {
      (apiClient.events.submitFeedback as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockEvent);
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const { result } = renderHook(() => useSubmitFeedback(), { wrapper });

      await act(async () => {
        await result.current.mutateAsync({
          eventId: 'event-123',
          rating: 'helpful',
        });
      });

      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['events'] });
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['event', 'event-123'] });
    });
  });

  describe('useUpdateFeedback', () => {
    it('updates feedback successfully', async () => {
      (apiClient.events.updateFeedback as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockFeedbackResponse);

      const { result } = renderHook(() => useUpdateFeedback(), { wrapper });

      await act(async () => {
        await result.current.mutateAsync({
          eventId: 'event-123',
          rating: 'not_helpful',
        });
      });

      expect(apiClient.events.updateFeedback).toHaveBeenCalledWith('event-123', {
        rating: 'not_helpful',
      });
    });

    it('updates feedback with correction', async () => {
      (apiClient.events.updateFeedback as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockFeedbackResponse);

      const { result } = renderHook(() => useUpdateFeedback(), { wrapper });

      await act(async () => {
        await result.current.mutateAsync({
          eventId: 'event-123',
          correction: 'Updated correction text',
        });
      });

      expect(apiClient.events.updateFeedback).toHaveBeenCalledWith('event-123', {
        correction: 'Updated correction text',
      });
    });

    it('clears correction with null value', async () => {
      (apiClient.events.updateFeedback as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockFeedbackResponse);

      const { result } = renderHook(() => useUpdateFeedback(), { wrapper });

      await act(async () => {
        await result.current.mutateAsync({
          eventId: 'event-123',
          correction: null,
        });
      });

      expect(apiClient.events.updateFeedback).toHaveBeenCalledWith('event-123', {
        correction: null,
      });
    });

    it('handles update error', async () => {
      const error = new Error('Update failed');
      (apiClient.events.updateFeedback as ReturnType<typeof vi.fn>).mockRejectedValueOnce(error);

      const { result } = renderHook(() => useUpdateFeedback(), { wrapper });

      await expect(
        result.current.mutateAsync({
          eventId: 'event-123',
          rating: 'not_helpful',
        })
      ).rejects.toThrow('Update failed');
    });
  });

  describe('useDeleteFeedback', () => {
    it('deletes feedback successfully', async () => {
      (apiClient.events.deleteFeedback as ReturnType<typeof vi.fn>).mockResolvedValueOnce(undefined);

      const { result } = renderHook(() => useDeleteFeedback(), { wrapper });

      await act(async () => {
        await result.current.mutateAsync('event-123');
      });

      expect(apiClient.events.deleteFeedback).toHaveBeenCalledWith('event-123');
    });

    it('handles delete error', async () => {
      const error = new Error('Delete failed');
      (apiClient.events.deleteFeedback as ReturnType<typeof vi.fn>).mockRejectedValueOnce(error);

      const { result } = renderHook(() => useDeleteFeedback(), { wrapper });

      await expect(result.current.mutateAsync('event-123')).rejects.toThrow('Delete failed');
    });

    it('invalidates event queries on success', async () => {
      (apiClient.events.deleteFeedback as ReturnType<typeof vi.fn>).mockResolvedValueOnce(undefined);
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const { result } = renderHook(() => useDeleteFeedback(), { wrapper });

      await act(async () => {
        await result.current.mutateAsync('event-123');
      });

      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['events'] });
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['event', 'event-123'] });
    });
  });
});
