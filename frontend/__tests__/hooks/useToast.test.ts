/**
 * useToast Hook Tests
 *
 * Tests for the toast notification utility hook.
 */
import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useToast } from '@/hooks/useToast';

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warning: vi.fn(),
  },
}));

import { toast } from 'sonner';

describe('useToast', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns all toast methods', () => {
    const { result } = renderHook(() => useToast());

    expect(result.current.showSuccess).toBeDefined();
    expect(result.current.showError).toBeDefined();
    expect(result.current.showInfo).toBeDefined();
    expect(result.current.showWarning).toBeDefined();
  });

  describe('showSuccess', () => {
    it('calls toast.success with the message', () => {
      const { result } = renderHook(() => useToast());

      act(() => {
        result.current.showSuccess('Operation successful');
      });

      expect(toast.success).toHaveBeenCalledWith('Operation successful');
      expect(toast.success).toHaveBeenCalledTimes(1);
    });
  });

  describe('showError', () => {
    it('calls toast.error with the message', () => {
      const { result } = renderHook(() => useToast());

      act(() => {
        result.current.showError('Something went wrong');
      });

      expect(toast.error).toHaveBeenCalledWith('Something went wrong');
      expect(toast.error).toHaveBeenCalledTimes(1);
    });
  });

  describe('showInfo', () => {
    it('calls toast.info with the message', () => {
      const { result } = renderHook(() => useToast());

      act(() => {
        result.current.showInfo('FYI: New feature available');
      });

      expect(toast.info).toHaveBeenCalledWith('FYI: New feature available');
      expect(toast.info).toHaveBeenCalledTimes(1);
    });
  });

  describe('showWarning', () => {
    it('calls toast.warning with the message', () => {
      const { result } = renderHook(() => useToast());

      act(() => {
        result.current.showWarning('Be careful!');
      });

      expect(toast.warning).toHaveBeenCalledWith('Be careful!');
      expect(toast.warning).toHaveBeenCalledTimes(1);
    });
  });

  describe('multiple calls', () => {
    it('can call multiple toast methods in sequence', () => {
      const { result } = renderHook(() => useToast());

      act(() => {
        result.current.showSuccess('Success 1');
        result.current.showError('Error 1');
        result.current.showInfo('Info 1');
      });

      expect(toast.success).toHaveBeenCalledWith('Success 1');
      expect(toast.error).toHaveBeenCalledWith('Error 1');
      expect(toast.info).toHaveBeenCalledWith('Info 1');
    });
  });
});
