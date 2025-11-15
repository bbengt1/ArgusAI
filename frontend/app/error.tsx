/**
 * Error boundary for React errors
 * This file creates an error boundary for the app router
 */

'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { AlertCircle } from 'lucide-react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log error to console (in production, send to error tracking service)
    console.error('Application error:', error);
  }, [error]);

  return (
    <div className="container mx-auto px-4 py-16 max-w-2xl">
      <div className="flex flex-col items-center text-center">
        <div className="p-4 bg-destructive/10 rounded-full mb-6">
          <AlertCircle className="h-12 w-12 text-destructive" />
        </div>

        <h1 className="text-3xl font-bold tracking-tight mb-4">
          Something went wrong!
        </h1>

        <p className="text-muted-foreground mb-8 max-w-md">
          An unexpected error occurred. Our team has been notified and is working on a fix.
        </p>

        {process.env.NODE_ENV === 'development' && (
          <details className="mb-8 w-full">
            <summary className="cursor-pointer text-sm font-medium mb-2">
              Error Details (Development Only)
            </summary>
            <pre className="bg-muted p-4 rounded-lg text-xs overflow-auto text-left">
              {error.message}
              {error.digest && `\nDigest: ${error.digest}`}
            </pre>
          </details>
        )}

        <div className="flex gap-4">
          <Button onClick={reset}>
            Try Again
          </Button>
          <Button variant="outline" onClick={() => window.location.href = '/cameras'}>
            Go to Cameras
          </Button>
        </div>
      </div>
    </div>
  );
}
