/**
 * Push Notifications Hook (Story P4-1.2, P4-1.3)
 *
 * Custom hook for managing Web Push notification subscriptions.
 * Handles:
 * - Service worker registration and lifecycle (P4-1.3)
 * - Permission state management
 * - Push subscription lifecycle
 * - VAPID key fetching
 * - Browser API interactions
 */

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { apiClient, ApiError } from '@/lib/api-client';
import type { PushNotificationStatus } from '@/types/push';

/**
 * Service worker path - must be at root to handle all notifications
 */
const SERVICE_WORKER_PATH = '/sw.js';

interface UsePushNotificationsReturn {
  /**
   * Current status of push notifications
   */
  status: PushNotificationStatus;
  /**
   * Whether push notifications are currently subscribed
   */
  isSubscribed: boolean;
  /**
   * Current notification permission state
   */
  permission: NotificationPermission | 'unsupported';
  /**
   * Error message if something went wrong
   */
  error: string | null;
  /**
   * Whether an operation is in progress
   */
  isLoading: boolean;
  /**
   * Device/browser info for display
   */
  deviceInfo: string | null;
  /**
   * Subscription endpoint (truncated) for display
   */
  subscriptionEndpoint: string | null;
  /**
   * Request notification permission and subscribe
   */
  subscribe: () => Promise<boolean>;
  /**
   * Unsubscribe from push notifications
   */
  unsubscribe: () => Promise<boolean>;
  /**
   * Send a test notification
   */
  sendTestNotification: () => Promise<boolean>;
  /**
   * Check if Push API is supported
   */
  isPushSupported: boolean;
  /**
   * Check if service worker is registered
   */
  hasServiceWorker: boolean;
  /**
   * Service worker registration (P4-1.3)
   */
  swRegistration: ServiceWorkerRegistration | null;
  /**
   * Register service worker manually (P4-1.3)
   */
  registerServiceWorker: () => Promise<ServiceWorkerRegistration | null>;
}

/**
 * Convert URL-safe base64 string to Uint8Array for applicationServerKey
 */
function urlBase64ToUint8Array(base64String: string): ArrayBuffer {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray.buffer;
}

/**
 * Get browser/device info for display
 */
function getDeviceInfo(): string {
  const ua = navigator.userAgent;

  // Detect browser
  let browser = 'Unknown Browser';
  if (ua.includes('Firefox')) {
    browser = 'Firefox';
  } else if (ua.includes('Edg/')) {
    browser = 'Edge';
  } else if (ua.includes('Chrome')) {
    browser = 'Chrome';
  } else if (ua.includes('Safari')) {
    browser = 'Safari';
  }

  // Detect platform
  let platform = 'Unknown';
  if (ua.includes('Windows')) {
    platform = 'Windows';
  } else if (ua.includes('Mac')) {
    platform = 'macOS';
  } else if (ua.includes('Linux')) {
    platform = 'Linux';
  } else if (ua.includes('iPhone') || ua.includes('iPad')) {
    platform = 'iOS';
  } else if (ua.includes('Android')) {
    platform = 'Android';
  }

  return `${browser} on ${platform}`;
}

/**
 * Hook for managing push notification subscriptions
 */
export function usePushNotifications(): UsePushNotificationsReturn {
  const [status, setStatus] = useState<PushNotificationStatus>('loading');
  const [permission, setPermission] = useState<NotificationPermission | 'unsupported'>('default');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [deviceInfo, setDeviceInfo] = useState<string | null>(null);
  const [subscriptionEndpoint, setSubscriptionEndpoint] = useState<string | null>(null);
  const [currentSubscription, setCurrentSubscription] = useState<PushSubscription | null>(null);
  const [swRegistration, setSwRegistration] = useState<ServiceWorkerRegistration | null>(null);

  // Track if SW registration is in progress to avoid duplicate registrations
  const swRegistrationInProgress = useRef(false);

  // Check browser support
  // Note: Push API requires HTTPS (secure context) except for localhost
  const isSecureContext = typeof window !== 'undefined' &&
    (window.isSecureContext || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

  const isPushSupported = typeof window !== 'undefined' &&
    'Notification' in window &&
    'serviceWorker' in navigator &&
    'PushManager' in window &&
    isSecureContext;

  const hasServiceWorker = typeof navigator !== 'undefined' &&
    'serviceWorker' in navigator;

  /**
   * Register service worker (P4-1.3)
   * Called automatically on mount, but can be called manually if needed
   */
  const registerServiceWorker = useCallback(async (): Promise<ServiceWorkerRegistration | null> => {
    if (!hasServiceWorker) {
      console.warn('[Push] Service workers not supported');
      return null;
    }

    // Prevent duplicate registration attempts
    if (swRegistrationInProgress.current) {
      console.log('[Push] SW registration already in progress');
      // Wait for existing registration
      try {
        const registration = await navigator.serviceWorker.ready;
        return registration;
      } catch {
        return null;
      }
    }

    swRegistrationInProgress.current = true;

    try {
      console.log('[Push] Registering service worker:', SERVICE_WORKER_PATH);

      // Check for existing registration first
      const existingRegistration = await navigator.serviceWorker.getRegistration(SERVICE_WORKER_PATH);

      if (existingRegistration) {
        console.log('[Push] Found existing SW registration');
        setSwRegistration(existingRegistration);

        // Check for updates in background
        existingRegistration.update().catch((err) => {
          console.warn('[Push] SW update check failed:', err);
        });

        return existingRegistration;
      }

      // Register new service worker
      const registration = await navigator.serviceWorker.register(SERVICE_WORKER_PATH, {
        scope: '/',
      });

      console.log('[Push] SW registered successfully:', registration.scope);
      setSwRegistration(registration);

      // Handle SW updates
      registration.addEventListener('updatefound', () => {
        console.log('[Push] SW update found');
        const newWorker = registration.installing;

        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            console.log('[Push] SW state changed:', newWorker.state);
            if (newWorker.state === 'activated') {
              console.log('[Push] New SW activated');
            }
          });
        }
      });

      // Wait for SW to be ready
      await navigator.serviceWorker.ready;
      console.log('[Push] SW is ready');

      return registration;
    } catch (err) {
      console.error('[Push] SW registration failed:', err);
      setError(`Service worker registration failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
      return null;
    } finally {
      swRegistrationInProgress.current = false;
    }
  }, [hasServiceWorker]);

  /**
   * Initialize and check current state
   * Also registers service worker if not already registered (P4-1.3)
   */
  const checkStatus = useCallback(async () => {
    // Check if push is supported
    if (!isPushSupported) {
      setStatus('unsupported');
      setPermission('unsupported');
      return;
    }

    // Check notification permission
    const currentPermission = Notification.permission;
    setPermission(currentPermission);

    if (currentPermission === 'denied') {
      setStatus('permission-denied');
      return;
    }

    // Register service worker if not already registered (P4-1.3)
    const registration = await registerServiceWorker();

    if (!registration) {
      console.warn('[Push] Service worker registration failed');
      setStatus('no-service-worker');
      return;
    }

    // Check for existing subscription
    try {
      const subscription = await registration.pushManager.getSubscription();

      if (subscription) {
        setCurrentSubscription(subscription);
        setSubscriptionEndpoint(subscription.endpoint);
        setDeviceInfo(getDeviceInfo());
        setStatus('subscribed');
      } else {
        setStatus('unsubscribed');
      }
    } catch (err) {
      console.warn('[Push] Error checking subscription:', err);
      setStatus('unsubscribed');
    }
  }, [isPushSupported, registerServiceWorker]);

  // Run initial check
  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  /**
   * Request permission and subscribe to push notifications
   */
  const subscribe = useCallback(async (): Promise<boolean> => {
    if (!isPushSupported) {
      setError('Push notifications are not supported in this browser');
      return false;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Request notification permission if not granted
      if (Notification.permission !== 'granted') {
        const result = await Notification.requestPermission();
        setPermission(result);

        if (result === 'denied') {
          setStatus('permission-denied');
          setError('Notification permission was denied. Please enable notifications in your browser settings.');
          return false;
        }

        if (result !== 'granted') {
          setError('Notification permission was not granted');
          return false;
        }
      }

      // Get service worker registration (P4-1.3: use registerServiceWorker)
      const registration = swRegistration || await registerServiceWorker();
      if (!registration) {
        setStatus('no-service-worker');
        setError('Service worker is not registered. Push notifications require a service worker.');
        return false;
      }

      // Get VAPID public key from backend
      const { public_key: vapidPublicKey } = await apiClient.push.getVapidPublicKey();

      // Subscribe to push
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidPublicKey),
      });

      // Extract keys from subscription
      const subscriptionJson = subscription.toJSON();
      if (!subscriptionJson.keys) {
        throw new Error('Failed to get subscription keys');
      }

      // Send subscription to backend
      await apiClient.push.subscribe({
        endpoint: subscription.endpoint,
        keys: {
          p256dh: subscriptionJson.keys.p256dh!,
          auth: subscriptionJson.keys.auth!,
        },
        device_name: navigator.userAgent,
      });

      // Update state
      setCurrentSubscription(subscription);
      setSubscriptionEndpoint(subscription.endpoint);
      setDeviceInfo(getDeviceInfo());
      setStatus('subscribed');

      return true;
    } catch (err) {
      console.error('Error subscribing to push:', err);

      if (err instanceof ApiError) {
        setError(err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to subscribe to push notifications');
      }

      setStatus('error');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [isPushSupported, swRegistration, registerServiceWorker]);

  /**
   * Unsubscribe from push notifications
   */
  const unsubscribe = useCallback(async (): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      if (currentSubscription) {
        // Unsubscribe from browser
        await currentSubscription.unsubscribe();

        // Remove from backend
        try {
          await apiClient.push.unsubscribe(currentSubscription.endpoint);
        } catch (err) {
          // Ignore 404 errors - subscription may already be removed
          if (err instanceof ApiError && err.statusCode !== 404) {
            throw err;
          }
        }
      }

      // Update state
      setCurrentSubscription(null);
      setSubscriptionEndpoint(null);
      setDeviceInfo(null);
      setStatus('unsubscribed');

      return true;
    } catch (err) {
      console.error('Error unsubscribing from push:', err);

      if (err instanceof ApiError) {
        setError(err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to unsubscribe from push notifications');
      }

      return false;
    } finally {
      setIsLoading(false);
    }
  }, [currentSubscription]);

  /**
   * Send a test notification
   */
  const sendTestNotification = useCallback(async (): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await apiClient.push.testNotification();

      if (!result.success && result.subscriptions_notified === 0) {
        setError('No subscriptions found. Enable notifications first.');
        return false;
      }

      return result.success;
    } catch (err) {
      console.error('Error sending test notification:', err);

      if (err instanceof ApiError) {
        setError(err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to send test notification');
      }

      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    status,
    isSubscribed: status === 'subscribed',
    permission,
    error,
    isLoading,
    deviceInfo,
    subscriptionEndpoint,
    subscribe,
    unsubscribe,
    sendTestNotification,
    isPushSupported,
    hasServiceWorker,
    swRegistration,
    registerServiceWorker,
  };
}
