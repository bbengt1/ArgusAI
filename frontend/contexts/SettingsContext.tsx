/**
 * Settings context for managing system-wide settings and preferences
 * BUG-003: Added systemName for dynamic branding across the app
 */

'use client';

import { createContext, useContext, useState, useCallback, ReactNode, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

export interface SystemSettings {
  // AI Provider Settings
  aiProvider: 'openai' | 'gemini' | 'claude';
  aiApiKey?: string;

  // Data Retention
  dataRetentionDays: number;

  // Motion Detection
  defaultMotionSensitivity: 'low' | 'medium' | 'high';

  // UI Preferences
  theme: 'light' | 'dark' | 'system';
  timezone: string;

  // System
  backendUrl: string;

  // BUG-003: System name for branding
  systemName: string;
}

interface SettingsContextType {
  settings: SystemSettings;
  isLoading: boolean;
  updateSetting: <K extends keyof SystemSettings>(key: K, value: SystemSettings[K]) => void;
  updateSettings: (newSettings: Partial<SystemSettings>) => void;
  resetSettings: () => void;
  refreshSystemName: () => Promise<void>;
}

const defaultSettings: SystemSettings = {
  aiProvider: 'openai',
  dataRetentionDays: 30,
  defaultMotionSensitivity: 'medium',
  theme: 'system',
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  backendUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  systemName: 'ArgusAI', // BUG-003: Default system name
};

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [isLoading, setIsLoading] = useState(true);

  // Load settings from localStorage on mount - only once during initialization
  const [settings, setSettings] = useState<SystemSettings>(() => {
    if (typeof window !== 'undefined') {
      const savedSettings = localStorage.getItem('system-settings');
      if (savedSettings) {
        try {
          const parsed = JSON.parse(savedSettings);
          return { ...defaultSettings, ...parsed };
        } catch (error) {
          console.error('Failed to load settings from localStorage:', error);
        }
      }
    }
    return defaultSettings;
  });

  // BUG-003: Fetch system name from API on mount
  const refreshSystemName = useCallback(async () => {
    try {
      const apiSettings = await apiClient.settings.get();
      if (apiSettings.system_name) {
        setSettings(prev => ({ ...prev, systemName: apiSettings.system_name }));
        // Update document title
        if (typeof document !== 'undefined') {
          document.title = apiSettings.system_name;
        }
      }
    } catch (error) {
      console.error('Failed to fetch system name:', error);
      // Keep default on error
    }
  }, []);

  // Fetch system name on mount
  useEffect(() => {
    refreshSystemName().finally(() => setIsLoading(false));
  }, [refreshSystemName]);

  // Save settings to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('system-settings', JSON.stringify(settings));
    // BUG-003: Also update document title when system name changes
    if (typeof document !== 'undefined' && settings.systemName) {
      document.title = settings.systemName;
    }
  }, [settings]);

  const updateSetting = useCallback(<K extends keyof SystemSettings>(
    key: K,
    value: SystemSettings[K]
  ) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  }, []);

  const updateSettings = useCallback((newSettings: Partial<SystemSettings>) => {
    setSettings(prev => ({ ...prev, ...newSettings }));
  }, []);

  const resetSettings = useCallback(() => {
    setSettings(defaultSettings);
    localStorage.removeItem('system-settings');
  }, []);

  return (
    <SettingsContext.Provider
      value={{
        settings,
        isLoading,
        updateSetting,
        updateSettings,
        resetSettings,
        refreshSystemName,
      }}
    >
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
}
