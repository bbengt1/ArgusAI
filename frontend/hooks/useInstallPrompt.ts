/**
 * PWA Install Prompt Hook (Story P4-1.5)
 *
 * Manages the PWA install prompt flow:
 * - Captures the beforeinstallprompt event
 * - Tracks install state (installable, installed)
 * - Provides promptInstall function to trigger native prompt
 * - Detects iOS for alternative instructions
 */

'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';

/**
 * Extended Event type for beforeinstallprompt
 */
interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[];
  readonly userChoice: Promise<{
    outcome: 'accepted' | 'dismissed';
    platform: string;
  }>;
  prompt(): Promise<void>;
}

/**
 * Install prompt state
 */
interface InstallPromptState {
  /** Whether the app can be installed (prompt available) */
  isInstallable: boolean;
  /** Whether the app is already installed (standalone mode) */
  isInstalled: boolean;
  /** Whether the device is iOS (needs different install flow) */
  isIOS: boolean;
  /** Whether the device is Android */
  isAndroid: boolean;
  /** Whether we're in standalone/installed mode */
  isStandalone: boolean;
  /** Trigger the install prompt */
  promptInstall: () => Promise<boolean>;
  /** Dismiss the install prompt (user declined) */
  dismissPrompt: () => void;
  /** Whether the prompt was dismissed by user in this session */
  wasDismissed: boolean;
}

const DISMISSED_KEY = 'pwa-install-dismissed';
const DISMISSED_EXPIRY_DAYS = 7;

/**
 * Check if install was dismissed recently
 */
function wasRecentlyDismissed(): boolean {
  if (typeof window === 'undefined') return false;

  const dismissed = localStorage.getItem(DISMISSED_KEY);
  if (!dismissed) return false;

  const dismissedTime = parseInt(dismissed, 10);
  const expiryTime = dismissedTime + DISMISSED_EXPIRY_DAYS * 24 * 60 * 60 * 1000;

  if (Date.now() > expiryTime) {
    localStorage.removeItem(DISMISSED_KEY);
    return false;
  }

  return true;
}

/**
 * Detect platform info (runs once on mount)
 */
function detectPlatform() {
  if (typeof window === 'undefined') {
    return { isIOS: false, isAndroid: false, isStandalone: false };
  }

  const userAgent = window.navigator.userAgent.toLowerCase();
  const isIOS = /iphone|ipad|ipod/.test(userAgent);
  const isAndroid = /android/.test(userAgent);
  const isStandalone =
    window.matchMedia('(display-mode: standalone)').matches ||
    (window.navigator as { standalone?: boolean }).standalone === true;

  return { isIOS, isAndroid, isStandalone };
}

/**
 * Hook for managing PWA install prompt
 */
export function useInstallPrompt(): InstallPromptState {
  // Detect platform once on mount
  const platform = useMemo(() => detectPlatform(), []);

  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isInstallable, setIsInstallable] = useState(false);
  const [isInstalled, setIsInstalled] = useState(platform.isStandalone);
  const [wasDismissed, setWasDismissed] = useState(() => wasRecentlyDismissed());

  useEffect(() => {
    // Only run in browser
    if (typeof window === 'undefined') return;

    // Already installed, no need for install prompt
    if (platform.isStandalone) {
      return;
    }

    // Check if user dismissed recently
    if (wasDismissed) {
      return;
    }

    // Listen for the beforeinstallprompt event
    const handleBeforeInstallPrompt = (e: Event) => {
      // Prevent the mini-infobar from appearing on mobile
      e.preventDefault();
      // Store the event for later use
      setDeferredPrompt(e as BeforeInstallPromptEvent);
      setIsInstallable(true);
      console.log('[PWA] Install prompt available');
    };

    // Listen for successful installs
    const handleAppInstalled = () => {
      console.log('[PWA] App was installed');
      setIsInstalled(true);
      setIsInstallable(false);
      setDeferredPrompt(null);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, [platform.isStandalone, wasDismissed]);

  /**
   * Trigger the install prompt
   */
  const promptInstall = useCallback(async (): Promise<boolean> => {
    if (!deferredPrompt) {
      console.log('[PWA] No deferred prompt available');
      return false;
    }

    try {
      // Show the install prompt
      await deferredPrompt.prompt();

      // Wait for the user's response
      const { outcome } = await deferredPrompt.userChoice;

      console.log('[PWA] Install prompt outcome:', outcome);

      if (outcome === 'accepted') {
        setIsInstalled(true);
        setIsInstallable(false);
      } else {
        // User dismissed, remember for a while
        localStorage.setItem(DISMISSED_KEY, Date.now().toString());
        setWasDismissed(true);
      }

      // Clear the deferred prompt
      setDeferredPrompt(null);

      return outcome === 'accepted';
    } catch (err) {
      console.error('[PWA] Error showing install prompt:', err);
      return false;
    }
  }, [deferredPrompt]);

  /**
   * Dismiss the install prompt
   */
  const dismissPrompt = useCallback(() => {
    localStorage.setItem(DISMISSED_KEY, Date.now().toString());
    setWasDismissed(true);
    setIsInstallable(false);
    console.log('[PWA] Install prompt dismissed by user');
  }, []);

  return {
    isInstallable,
    isInstalled,
    isIOS: platform.isIOS,
    isAndroid: platform.isAndroid,
    isStandalone: platform.isStandalone,
    promptInstall,
    dismissPrompt,
    wasDismissed,
  };
}
