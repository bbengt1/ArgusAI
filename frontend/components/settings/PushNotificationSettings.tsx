/**
 * Push Notification Settings Component (Story P4-1.2)
 *
 * Features:
 * - Enable/disable push notifications toggle
 * - Permission request flow
 * - Test notification button
 * - Device info display when subscribed
 * - Notification preview
 * - Permission denied guidance
 */

'use client';

import { useState } from 'react';
import { toast } from 'sonner';
import {
  Bell,
  BellOff,
  Loader2,
  Send,
  AlertTriangle,
  CheckCircle2,
  Smartphone,
  Info,
  ExternalLink,
} from 'lucide-react';

import { usePushNotifications } from '@/hooks/usePushNotifications';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { NotificationPreferences } from './NotificationPreferences';

/**
 * Notification Preview Component
 * Shows a mockup of what notifications will look like
 */
function NotificationPreview() {
  return (
    <div className="mt-4 space-y-2">
      <p className="text-sm text-muted-foreground">
        This is what notifications will look like:
      </p>
      <div className="rounded-lg border bg-card p-3 shadow-sm max-w-sm">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
            <Bell className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1 space-y-1">
            <p className="text-sm font-medium">Front Door: Motion Detected</p>
            <p className="text-xs text-muted-foreground">
              Person approaching the front door with a package
            </p>
            <p className="text-xs text-muted-foreground/70">Just now</p>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Permission Denied Banner Component
 * Shows guidance for re-enabling notifications
 */
function PermissionDeniedBanner() {
  const [expanded, setExpanded] = useState(false);

  return (
    <Alert variant="destructive" className="mt-4">
      <AlertTriangle className="h-4 w-4" />
      <AlertTitle>Notifications Blocked</AlertTitle>
      <AlertDescription className="mt-2">
        <p>
          You have blocked notifications for this site. To enable push notifications,
          you need to allow them in your browser settings.
        </p>

        {expanded && (
          <div className="mt-3 space-y-3 text-sm">
            <div>
              <p className="font-medium">Chrome / Edge:</p>
              <ol className="ml-4 list-decimal space-y-1">
                <li>Click the lock icon in the address bar</li>
                <li>Find &quot;Notifications&quot; setting</li>
                <li>Change to &quot;Allow&quot;</li>
                <li>Refresh this page</li>
              </ol>
            </div>
            <div>
              <p className="font-medium">Firefox:</p>
              <ol className="ml-4 list-decimal space-y-1">
                <li>Click the lock icon in the address bar</li>
                <li>Click &quot;Clear Permissions and Reload&quot; or find Notifications</li>
                <li>Remove the block</li>
                <li>Refresh this page</li>
              </ol>
            </div>
            <div>
              <p className="font-medium">Safari:</p>
              <ol className="ml-4 list-decimal space-y-1">
                <li>Go to Safari → Settings → Websites → Notifications</li>
                <li>Find this website and change to &quot;Allow&quot;</li>
                <li>Refresh this page</li>
              </ol>
            </div>
          </div>
        )}

        <Button
          variant="link"
          size="sm"
          className="mt-2 h-auto p-0 text-destructive-foreground"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? 'Hide instructions' : 'Show how to re-enable'}
          <ExternalLink className="ml-1 h-3 w-3" />
        </Button>
      </AlertDescription>
    </Alert>
  );
}

/**
 * Unsupported Browser Banner
 */
function UnsupportedBanner() {
  // Check if the issue is HTTP vs HTTPS
  const isInsecureOrigin = typeof window !== 'undefined' &&
    !window.isSecureContext &&
    window.location.hostname !== 'localhost' &&
    window.location.hostname !== '127.0.0.1';

  return (
    <Alert className="mt-4">
      <Info className="h-4 w-4" />
      <AlertTitle>Push Notifications Not Available</AlertTitle>
      <AlertDescription>
        {isInsecureOrigin ? (
          <>
            <p>
              Push notifications require a <strong>secure connection (HTTPS)</strong>.
              You are currently accessing this site over HTTP.
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              To enable push notifications, configure HTTPS for your server or access via localhost.
            </p>
          </>
        ) : (
          <>
            <p>
              Your browser does not support push notifications. To receive notifications,
              please use a modern browser like Chrome, Firefox, Edge, or Safari 16+.
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              On iOS, push notifications require installing this app as a PWA (Add to Home Screen).
            </p>
          </>
        )}
      </AlertDescription>
    </Alert>
  );
}

/**
 * No Service Worker Banner
 */
function NoServiceWorkerBanner() {
  return (
    <Alert className="mt-4">
      <Info className="h-4 w-4" />
      <AlertTitle>Service Worker Required</AlertTitle>
      <AlertDescription>
        <p>
          Push notifications require a service worker, which is not yet configured.
          This feature will be fully available soon.
        </p>
        <p className="mt-2 text-sm text-muted-foreground">
          A service worker will be added in a future update to enable push notifications.
        </p>
      </AlertDescription>
    </Alert>
  );
}

/**
 * Main Push Notification Settings Component
 */
export function PushNotificationSettings() {
  const {
    status,
    isSubscribed,
    permission,
    error,
    isLoading,
    deviceInfo,
    subscriptionEndpoint,
    subscribe,
    unsubscribe,
    sendTestNotification,
    isPushSupported,
  } = usePushNotifications();

  const [isSendingTest, setIsSendingTest] = useState(false);

  const handleToggle = async (enabled: boolean) => {
    if (enabled) {
      const success = await subscribe();
      if (success) {
        toast.success('Push notifications enabled', {
          description: 'You will now receive notifications for security events.',
        });
      } else if (permission === 'denied') {
        toast.error('Permission denied', {
          description: 'Please enable notifications in your browser settings.',
        });
      }
    } else {
      const success = await unsubscribe();
      if (success) {
        toast.success('Push notifications disabled', {
          description: 'You will no longer receive push notifications.',
        });
      }
    }
  };

  const handleSendTest = async () => {
    setIsSendingTest(true);
    try {
      const success = await sendTestNotification();
      if (success) {
        toast.success('Test notification sent', {
          description: 'Check your device for the notification.',
        });
      } else {
        toast.error('Test failed', {
          description: error || 'Failed to send test notification.',
        });
      }
    } finally {
      setIsSendingTest(false);
    }
  };

  // Determine status display
  const getStatusBadge = () => {
    switch (status) {
      case 'loading':
        return <Badge variant="secondary"><Loader2 className="mr-1 h-3 w-3 animate-spin" />Checking...</Badge>;
      case 'subscribed':
        return <Badge variant="default" className="bg-green-600"><CheckCircle2 className="mr-1 h-3 w-3" />Enabled</Badge>;
      case 'unsubscribed':
        return <Badge variant="secondary"><BellOff className="mr-1 h-3 w-3" />Disabled</Badge>;
      case 'permission-denied':
        return <Badge variant="destructive"><AlertTriangle className="mr-1 h-3 w-3" />Blocked</Badge>;
      case 'unsupported':
        return <Badge variant="secondary">Not Supported</Badge>;
      case 'no-service-worker':
        return <Badge variant="secondary">Setup Required</Badge>;
      case 'error':
        return <Badge variant="destructive">Error</Badge>;
      default:
        return null;
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Push Notifications
            </CardTitle>
            <CardDescription>
              Receive real-time alerts on your device when security events are detected
            </CardDescription>
          </div>
          {getStatusBadge()}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Enable/Disable Toggle */}
        <div className="flex items-center justify-between rounded-lg border p-4">
          <div className="space-y-0.5">
            <Label htmlFor="push-enabled" className="text-base font-medium">
              Enable Notifications
            </Label>
            <p className="text-sm text-muted-foreground">
              Get notified about motion, people, vehicles, and packages
            </p>
          </div>
          <Switch
            id="push-enabled"
            checked={isSubscribed}
            onCheckedChange={handleToggle}
            disabled={isLoading || status === 'loading' || status === 'unsupported' || status === 'no-service-worker'}
          />
        </div>

        {/* Show appropriate banner based on status */}
        {status === 'unsupported' && <UnsupportedBanner />}
        {status === 'no-service-worker' && <NoServiceWorkerBanner />}
        {status === 'permission-denied' && <PermissionDeniedBanner />}

        {/* Device Info (when subscribed) */}
        {isSubscribed && deviceInfo && (
          <div className="flex items-center gap-3 rounded-lg bg-muted/50 p-3">
            <Smartphone className="h-5 w-5 text-muted-foreground" />
            <div className="flex-1">
              <p className="text-sm font-medium">Subscribed Device</p>
              <p className="text-sm text-muted-foreground">{deviceInfo}</p>
            </div>
            <CheckCircle2 className="h-5 w-5 text-green-600" />
          </div>
        )}

        {/* Test Notification Button (when subscribed) */}
        {isSubscribed && (
          <div className="flex items-center justify-between rounded-lg border p-4">
            <div className="space-y-0.5">
              <p className="text-sm font-medium">Test Notification</p>
              <p className="text-sm text-muted-foreground">
                Send a test to verify notifications are working
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleSendTest}
              disabled={isSendingTest}
            >
              {isSendingTest ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Sending...
                </>
              ) : (
                <>
                  <Send className="mr-2 h-4 w-4" />
                  Send Test
                </>
              )}
            </Button>
          </div>
        )}

        {/* Notification Preferences (when subscribed) - P4-1.4 */}
        <NotificationPreferences
          endpoint={subscriptionEndpoint}
          isSubscribed={isSubscribed}
        />

        {/* Error Display */}
        {error && status !== 'permission-denied' && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Notification Preview */}
        {isPushSupported && status !== 'unsupported' && status !== 'no-service-worker' && (
          <NotificationPreview />
        )}

        {/* Info about notification types */}
        <div className="rounded-lg bg-muted/30 p-3">
          <p className="text-xs text-muted-foreground">
            You will receive notifications for motion events, person detection, vehicle detection,
            package detection, and doorbell rings from your enabled cameras.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
