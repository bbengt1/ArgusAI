/**
 * Offline Page (Story P4-1.5)
 *
 * Displayed when the user is offline and the requested page is not cached.
 */

'use client';

import { WifiOff, RefreshCw, Home } from 'lucide-react';
import Link from 'next/link';

export default function OfflinePage() {
  return (
    <div className="flex min-h-[80vh] flex-col items-center justify-center px-4">
      <div className="text-center max-w-md">
        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-muted">
          <WifiOff className="h-10 w-10 text-muted-foreground" />
        </div>

        <h1 className="mb-2 text-2xl font-bold">You&apos;re Offline</h1>

        <p className="mb-6 text-muted-foreground">
          It looks like you&apos;ve lost your internet connection. Some features may be
          unavailable until you&apos;re back online.
        </p>

        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">
            Don&apos;t worry - any cached events and data are still available.
          </p>

          <div className="flex flex-col gap-3 sm:flex-row sm:justify-center">
            <button
              onClick={() => window.location.reload()}
              className="inline-flex items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              <RefreshCw className="h-4 w-4" />
              Try Again
            </button>

            <Link
              href="/"
              className="inline-flex items-center justify-center gap-2 rounded-md border border-input bg-background px-4 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground"
            >
              <Home className="h-4 w-4" />
              Go Home
            </Link>
          </div>
        </div>

        <div className="mt-8 rounded-lg border bg-muted/50 p-4">
          <h2 className="mb-2 font-semibold">What you can do offline:</h2>
          <ul className="text-sm text-muted-foreground text-left space-y-1">
            <li>• View previously loaded events</li>
            <li>• Browse cached camera information</li>
            <li>• Access settings and preferences</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
