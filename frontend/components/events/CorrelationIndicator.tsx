/**
 * CorrelationIndicator component - displays multi-camera event correlation info
 * Story P2-4.4: Display Correlated Events in Dashboard
 *
 * Renders at the bottom of EventCard when an event has correlated events from
 * other cameras. Shows a link chain icon and clickable camera names that scroll
 * to and highlight the related events.
 */

'use client';

import { memo } from 'react';
import { Link2 } from 'lucide-react';
import type { ICorrelatedEvent } from '@/types/event';

interface CorrelationIndicatorProps {
  /** Array of correlated events from other cameras */
  correlatedEvents: ICorrelatedEvent[];
  /** Callback when a camera name is clicked - receives event ID to scroll to */
  onEventClick: (eventId: string) => void;
}

/**
 * CorrelationIndicator - shows "Also captured by: Camera A, Camera B" with
 * clickable camera names that scroll to the related event in the timeline.
 */
export const CorrelationIndicator = memo(function CorrelationIndicator({
  correlatedEvents,
  onEventClick,
}: CorrelationIndicatorProps) {
  // AC8: Don't render if no correlated events
  if (!correlatedEvents || correlatedEvents.length === 0) {
    return null;
  }

  const handleCameraClick = (e: React.MouseEvent, eventId: string) => {
    e.stopPropagation(); // Prevent card click from triggering
    onEventClick(eventId);
  };

  return (
    <div className="flex items-center gap-1.5 pt-2 border-t border-gray-100 mt-2">
      {/* Link chain icon */}
      <Link2 className="w-4 h-4 text-blue-500 flex-shrink-0" aria-hidden="true" />

      {/* "Also captured by:" text */}
      <span className="text-xs text-muted-foreground">Also captured by:</span>

      {/* Clickable camera names */}
      <div className="flex items-center gap-1 flex-wrap">
        {correlatedEvents.map((event, index) => (
          <span key={event.id} className="inline-flex items-center">
            <button
              type="button"
              onClick={(e) => handleCameraClick(e, event.id)}
              className="text-xs font-medium text-blue-600 hover:text-blue-800 hover:underline focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 rounded"
              aria-label={`Scroll to event from ${event.camera_name}`}
            >
              {event.camera_name}
            </button>
            {/* Add comma separator between camera names, except for last one */}
            {index < correlatedEvents.length - 1 && (
              <span className="text-xs text-muted-foreground">,</span>
            )}
          </span>
        ))}
      </div>
    </div>
  );
});
