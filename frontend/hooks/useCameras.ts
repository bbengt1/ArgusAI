/**
 * Custom hook for fetching and managing camera list
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient, ApiError } from '@/lib/api-client';
import type { ICamera } from '@/types/camera';

interface UseCamerasOptions {
  /**
   * Optional filter for enabled/disabled cameras
   */
  is_enabled?: boolean;
  /**
   * Whether to fetch automatically on mount
   */
  autoFetch?: boolean;
}

interface UseCamerasReturn {
  /**
   * Array of cameras
   */
  cameras: ICamera[];
  /**
   * Loading state
   */
  loading: boolean;
  /**
   * Error message if fetch failed
   */
  error: string | null;
  /**
   * Refresh camera list
   */
  refresh: () => Promise<void>;
}

/**
 * Hook to fetch and manage camera list
 * @param options Fetch options (filters, autoFetch)
 * @returns Camera list state and refresh function
 */
export function useCameras(
  options: UseCamerasOptions = { autoFetch: true }
): UseCamerasReturn {
  const [cameras, setCameras] = useState<ICamera[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCameras = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const filters = options.is_enabled !== undefined
        ? { is_enabled: options.is_enabled }
        : undefined;

      const data = await apiClient.cameras.list(filters);
      setCameras(data);
    } catch (err) {
      const errorMessage =
        err instanceof ApiError
          ? err.message
          : 'Failed to fetch cameras';
      setError(errorMessage);
      setCameras([]);
    } finally {
      setLoading(false);
    }
  }, [options.is_enabled]);

  // Auto-fetch on mount if enabled
  useEffect(() => {
    if (options.autoFetch !== false) {
      fetchCameras();
    }
  }, [options.autoFetch, fetchCameras]);

  return {
    cameras,
    loading,
    error,
    refresh: fetchCameras,
  };
}
