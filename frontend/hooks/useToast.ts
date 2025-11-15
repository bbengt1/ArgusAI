/**
 * Custom hook for toast notifications using sonner
 * Provides a simple API for showing success/error messages
 */

'use client';

import { toast } from 'sonner';

interface UseToastReturn {
  /**
   * Show success toast
   * @param message Success message
   */
  showSuccess: (message: string) => void;
  /**
   * Show error toast
   * @param message Error message
   */
  showError: (message: string) => void;
  /**
   * Show info toast
   * @param message Info message
   */
  showInfo: (message: string) => void;
  /**
   * Show warning toast
   * @param message Warning message
   */
  showWarning: (message: string) => void;
}

/**
 * Hook to display toast notifications
 * @returns Toast notification methods
 */
export function useToast(): UseToastReturn {
  return {
    showSuccess: (message: string) => {
      toast.success(message);
    },
    showError: (message: string) => {
      toast.error(message);
    },
    showInfo: (message: string) => {
      toast.info(message);
    },
    showWarning: (message: string) => {
      toast.warning(message);
    },
  };
}
