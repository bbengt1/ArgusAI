/**
 * SourceTypeBadge - displays the source type of an event (Protect, RTSP, USB)
 *
 * Used in EventCard to indicate which camera system captured the event.
 * Follows UX spec Section 10.5 for styling and icon selection.
 */

'use client';

import { Shield, Camera, Usb } from 'lucide-react';

export type SourceType = 'protect' | 'rtsp' | 'usb';

interface SourceTypeBadgeProps {
  sourceType: SourceType;
}

const SOURCE_CONFIG: Record<SourceType, { icon: typeof Shield; label: string }> = {
  protect: { icon: Shield, label: 'Protect' },
  rtsp: { icon: Camera, label: 'RTSP' },
  usb: { icon: Usb, label: 'USB' },
};

export function SourceTypeBadge({ sourceType }: SourceTypeBadgeProps) {
  const config = SOURCE_CONFIG[sourceType];

  if (!config) {
    return null;
  }

  const Icon = config.icon;

  return (
    <div className="flex items-center gap-1 text-xs text-muted-foreground">
      <Icon className="h-3 w-3" aria-hidden="true" />
      <span>{config.label}</span>
      <span className="sr-only">Source: {config.label}</span>
    </div>
  );
}
