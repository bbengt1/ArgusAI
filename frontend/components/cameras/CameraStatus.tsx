/**
 * Camera connection status indicator
 * Shows colored badge with status text and icon
 */

import { Circle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface CameraStatusProps {
  /**
   * Whether camera is enabled
   */
  isEnabled: boolean;
  /**
   * Optional: Is camera currently connected (derived from is_enabled for MVP)
   */
  isConnected?: boolean;
  /**
   * Optional: Custom className
   */
  className?: string;
}

/**
 * Camera status badge component
 * - Green: Connected (enabled)
 * - Red: Disconnected (!enabled)
 * - Gray: Disabled (placeholder for future real-time status via WebSocket)
 */
export function CameraStatus({
  isEnabled,
  isConnected,
  className,
}: CameraStatusProps) {
  // For MVP: use is_enabled as proxy for connection status
  // Future enhancement (F6.6): Real-time WebSocket status
  const connected = isConnected ?? isEnabled;
  const status = isEnabled ? (connected ? 'connected' : 'disconnected') : 'disabled';

  const statusConfig = {
    connected: {
      label: 'Connected',
      color: 'text-green-600',
      bgColor: 'bg-green-50 border-green-200',
      fillColor: 'fill-green-600',
    },
    disconnected: {
      label: 'Disconnected',
      color: 'text-red-600',
      bgColor: 'bg-red-50 border-red-200',
      fillColor: 'fill-red-600',
    },
    disabled: {
      label: 'Disabled',
      color: 'text-gray-600',
      bgColor: 'bg-gray-50 border-gray-200',
      fillColor: 'fill-gray-600',
    },
  };

  const config = statusConfig[status];

  return (
    <Badge
      variant="outline"
      className={cn(
        'flex items-center gap-1.5 px-2.5 py-1',
        config.bgColor,
        config.color,
        className
      )}
    >
      <Circle className={cn('h-2 w-2', config.fillColor)} />
      <span className="text-xs font-medium">{config.label}</span>
    </Badge>
  );
}
