/**
 * Service Worker Management Hook (Story P4-1.5)
 *
 * Manages service worker lifecycle:
 * - Registers the service worker
 * - Tracks update availability
 * - Provides refresh function for updates
 */

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

interface ServiceWorkerState {
  /** Whether the service worker is registered */
  isRegistered: boolean;
  /** Whether an update is available */
  updateAvailable: boolean;
  /** The current service worker version */
  version: string | null;
  /** Registration object */
  registration: ServiceWorkerRegistration | null;
  /** Trigger update (reload page with new SW) */
  applyUpdate: () => void;
  /** Manually check for updates */
  checkForUpdate: () => Promise<void>;
}

/**
 * Hook for managing service worker
 */
export function useServiceWorker(): ServiceWorkerState {
  const [isRegistered, setIsRegistered] = useState(false);
  const [updateAvailable, setUpdateAvailable] = useState(false);
  const [version, setVersion] = useState<string | null>(null);
  const [registration, setRegistration] = useState<ServiceWorkerRegistration | null>(null);

  // Use ref to avoid stale closure in useCallback
  const registrationRef = useRef<ServiceWorkerRegistration | null>(null);

  /**
   * Get version from service worker
   */
  const getVersion = useCallback((sw: ServiceWorker) => {
    const messageChannel = new MessageChannel();

    messageChannel.port1.onmessage = (event) => {
      if (event.data?.version) {
        setVersion(event.data.version);
      }
    };

    sw.postMessage({ type: 'GET_VERSION' }, [messageChannel.port2]);
  }, []);

  useEffect(() => {
    // Only run in browser with service worker support
    if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
      return;
    }

    let mounted = true;

    const registerSW = async () => {
      try {
        // Register the service worker
        const reg = await navigator.serviceWorker.register('/sw.js', {
          scope: '/',
        });

        if (!mounted) return;

        console.log('[SW Hook] Service worker registered');
        registrationRef.current = reg;
        setRegistration(reg);
        setIsRegistered(true);

        // Get version from current SW
        if (reg.active) {
          getVersion(reg.active);
        }

        // Listen for updates
        reg.addEventListener('updatefound', () => {
          const newWorker = reg.installing;
          if (!newWorker) return;

          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New service worker is installed, update available
              console.log('[SW Hook] Update available');
              if (mounted) {
                setUpdateAvailable(true);
              }
            }
          });
        });
      } catch (err) {
        console.error('[SW Hook] Registration failed:', err);
      }
    };

    // Listen for messages from service worker
    const handleMessage = (event: MessageEvent) => {
      if (event.data?.type === 'SW_UPDATED') {
        console.log('[SW Hook] Received SW_UPDATED message:', event.data.version);
        if (mounted) {
          setVersion(event.data.version);
          setUpdateAvailable(true);
        }
      }
    };

    navigator.serviceWorker.addEventListener('message', handleMessage);
    registerSW();

    return () => {
      mounted = false;
      navigator.serviceWorker.removeEventListener('message', handleMessage);
    };
  }, [getVersion]);

  /**
   * Apply the update by reloading
   */
  const applyUpdate = useCallback(() => {
    const reg = registrationRef.current;
    if (!reg?.waiting) {
      // No waiting worker, just reload
      window.location.reload();
      return;
    }

    // Tell the waiting SW to skip waiting
    reg.waiting.postMessage({ type: 'SKIP_WAITING' });

    // Reload once the new SW takes over
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      window.location.reload();
    });
  }, []);

  /**
   * Manually check for updates
   */
  const checkForUpdate = useCallback(async () => {
    const reg = registrationRef.current;
    if (!reg) return;

    try {
      await reg.update();
      console.log('[SW Hook] Update check complete');
    } catch (err) {
      console.error('[SW Hook] Update check failed:', err);
    }
  }, []);

  return {
    isRegistered,
    updateAvailable,
    version,
    registration,
    applyUpdate,
    checkForUpdate,
  };
}
