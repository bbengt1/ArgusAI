/**
 * Camera preview card component
 * Displays camera info with status indicator and action buttons
 */

'use client';

import Link from 'next/link';
import { Video, Edit, Trash2 } from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CameraStatus } from './CameraStatus';
import type { ICamera } from '@/types/camera';
import { format } from 'date-fns';

interface CameraPreviewProps {
  /**
   * Camera object
   */
  camera: ICamera;
  /**
   * Delete button click handler
   */
  onDelete: (camera: ICamera) => void;
}

/**
 * Camera preview card
 * Shows camera name, type, status, and action buttons
 */
export function CameraPreview({ camera, onDelete }: CameraPreviewProps) {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-50 rounded-lg">
              <Video className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-lg">{camera.name}</h3>
              <p className="text-sm text-muted-foreground capitalize">
                {camera.type === 'rtsp' ? 'RTSP Camera' : 'USB Camera'}
              </p>
            </div>
          </div>
          <CameraStatus isEnabled={camera.is_enabled} />
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Camera details */}
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="text-muted-foreground">Frame Rate:</span>
            <span className="ml-2 font-medium">{camera.frame_rate} FPS</span>
          </div>
          <div>
            <span className="text-muted-foreground">Sensitivity:</span>
            <span className="ml-2 font-medium capitalize">
              {camera.motion_sensitivity}
            </span>
          </div>
        </div>

        {/* Updated timestamp */}
        <div className="text-xs text-muted-foreground">
          Updated: {format(new Date(camera.updated_at), 'MMM d, yyyy h:mm a')}
        </div>

        {/* Action buttons */}
        <div className="flex gap-2 pt-2">
          <Button
            asChild
            variant="outline"
            size="sm"
            className="flex-1"
          >
            <Link href={`/cameras/${camera.id}`}>
              <Edit className="h-4 w-4 mr-2" />
              Edit
            </Link>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onDelete(camera)}
            className="text-destructive hover:text-destructive"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
