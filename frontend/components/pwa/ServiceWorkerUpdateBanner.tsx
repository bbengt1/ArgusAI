/**
 * Service Worker Update Banner (Story P4-1.5)
 *
 * Shows a toast/banner when a new service worker version is available.
 * User can click to refresh and get the new version.
 */

'use client';

import { RefreshCw, X } from 'lucide-react';
import { useServiceWorker } from '@/hooks/useServiceWorker';
import { Button } from '@/components/ui/button';
import { useState } from 'react';

/**
 * Service Worker Update Banner
 */
export function ServiceWorkerUpdateBanner() {
  const { updateAvailable, applyUpdate, version } = useServiceWorker();
  const [dismissed, setDismissed] = useState(false);

  // Don't show if no update or dismissed
  if (!updateAvailable || dismissed) {
    return null;
  }

  return (
    <div className="fixed top-4 left-1/2 -translate-x-1/2 z-[100] animate-in slide-in-from-top duration-300">
      <div className="flex items-center gap-3 rounded-lg border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80 px-4 py-3 shadow-lg">
        <RefreshCw className="h-5 w-5 text-primary animate-spin-slow" />
        <div className="text-sm">
          <p className="font-medium">Update Available</p>
          <p className="text-muted-foreground">
            {version ? `Version ${version}` : 'A new version is ready'}
          </p>
        </div>
        <div className="flex items-center gap-2 ml-2">
          <Button size="sm" onClick={applyUpdate}>
            Refresh
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => setDismissed(true)}
          >
            <X className="h-4 w-4" />
            <span className="sr-only">Dismiss</span>
          </Button>
        </div>
      </div>
    </div>
  );
}

export default ServiceWorkerUpdateBanner;
