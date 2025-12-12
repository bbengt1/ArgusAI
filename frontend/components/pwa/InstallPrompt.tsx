/**
 * PWA Install Prompt Component (Story P4-1.5)
 *
 * Shows install prompt banner/modal for eligible users:
 * - Android/Chrome: Native install prompt
 * - iOS: Instructions to use Share > Add to Home Screen
 * - Already installed: Hidden
 */

'use client';

import { useState } from 'react';
import { Download, X, Share, PlusSquare, Smartphone } from 'lucide-react';
import { useInstallPrompt } from '@/hooks/useInstallPrompt';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface InstallPromptProps {
  /**
   * Variant of the prompt
   * - 'banner': Fixed banner at bottom of screen
   * - 'inline': Inline component (e.g., in settings)
   */
  variant?: 'banner' | 'inline';
}

/**
 * Install Prompt Component
 */
export function InstallPrompt({ variant = 'banner' }: InstallPromptProps) {
  const {
    isInstallable,
    isInstalled,
    isIOS,
    isStandalone,
    promptInstall,
    dismissPrompt,
    wasDismissed,
  } = useInstallPrompt();

  const [showIOSDialog, setShowIOSDialog] = useState(false);
  const [isInstalling, setIsInstalling] = useState(false);

  // Don't show if already installed or dismissed
  if (isInstalled || isStandalone || wasDismissed) {
    return null;
  }

  // Don't show banner variant if not installable and not iOS
  if (variant === 'banner' && !isInstallable && !isIOS) {
    return null;
  }

  const handleInstall = async () => {
    if (isIOS) {
      setShowIOSDialog(true);
      return;
    }

    setIsInstalling(true);
    try {
      await promptInstall();
    } finally {
      setIsInstalling(false);
    }
  };

  const handleDismiss = () => {
    dismissPrompt();
  };

  // Inline variant for settings page
  if (variant === 'inline') {
    if (isInstalled || isStandalone) {
      return (
        <div className="rounded-lg border bg-muted/50 p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-500/10">
              <Smartphone className="h-5 w-5 text-green-500" />
            </div>
            <div>
              <p className="font-medium">App Installed</p>
              <p className="text-sm text-muted-foreground">
                You&apos;re using the installed app version
              </p>
            </div>
          </div>
        </div>
      );
    }

    return (
      <>
        <div className="rounded-lg border p-4">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
              <Download className="h-5 w-5 text-primary" />
            </div>
            <div className="flex-1">
              <p className="font-medium">Install App</p>
              <p className="text-sm text-muted-foreground mb-3">
                {isIOS
                  ? 'Add to your home screen for quick access'
                  : 'Install the app for faster access and offline support'}
              </p>
              <Button onClick={handleInstall} disabled={isInstalling} size="sm">
                {isIOS ? (
                  <>
                    <Share className="mr-2 h-4 w-4" />
                    How to Install
                  </>
                ) : (
                  <>
                    <Download className="mr-2 h-4 w-4" />
                    {isInstalling ? 'Installing...' : 'Install'}
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>

        <IOSInstallDialog open={showIOSDialog} onOpenChange={setShowIOSDialog} />
      </>
    );
  }

  // Banner variant (fixed at bottom)
  return (
    <>
      <div className="fixed bottom-0 left-0 right-0 z-50 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80 p-4 shadow-lg animate-in slide-in-from-bottom duration-300">
        <div className="container mx-auto flex items-center justify-between gap-4 max-w-2xl">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary">
              <Download className="h-5 w-5 text-primary-foreground" />
            </div>
            <div className="min-w-0">
              <p className="font-medium truncate">Install ArgusAI</p>
              <p className="text-sm text-muted-foreground truncate">
                {isIOS ? 'Add to home screen' : 'Quick access & offline support'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" onClick={handleDismiss} className="shrink-0">
              <X className="h-4 w-4" />
              <span className="sr-only">Dismiss</span>
            </Button>
            <Button onClick={handleInstall} disabled={isInstalling} size="sm" className="shrink-0">
              {isIOS ? 'How?' : isInstalling ? '...' : 'Install'}
            </Button>
          </div>
        </div>
      </div>

      <IOSInstallDialog open={showIOSDialog} onOpenChange={setShowIOSDialog} />
    </>
  );
}

/**
 * iOS Install Instructions Dialog
 */
function IOSInstallDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Install on iOS</DialogTitle>
          <DialogDescription>
            Follow these steps to add ArgusAI to your home screen
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted text-sm font-medium">
              1
            </div>
            <div>
              <p className="font-medium">Tap the Share button</p>
              <p className="text-sm text-muted-foreground">
                Look for the{' '}
                <Share className="inline h-4 w-4 align-text-bottom" /> icon at the
                bottom of Safari
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted text-sm font-medium">
              2
            </div>
            <div>
              <p className="font-medium">Select &quot;Add to Home Screen&quot;</p>
              <p className="text-sm text-muted-foreground">
                Scroll down in the share menu and tap{' '}
                <PlusSquare className="inline h-4 w-4 align-text-bottom" /> Add to
                Home Screen
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted text-sm font-medium">
              3
            </div>
            <div>
              <p className="font-medium">Tap &quot;Add&quot;</p>
              <p className="text-sm text-muted-foreground">
                The app will appear on your home screen
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-lg bg-muted p-3">
          <p className="text-sm text-muted-foreground">
            <strong>Note:</strong> Make sure you&apos;re using Safari. Other browsers on
            iOS don&apos;t support adding to home screen.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default InstallPrompt;
