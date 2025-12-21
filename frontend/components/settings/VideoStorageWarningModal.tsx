/**
 * Video Storage Warning Modal Component
 * Story P8-3.2: Displays warning about storage implications when enabling video storage
 */

'use client';

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { HardDrive, AlertTriangle } from 'lucide-react';

interface VideoStorageWarningModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  onCancel: () => void;
}

export function VideoStorageWarningModal({
  open,
  onOpenChange,
  onConfirm,
  onCancel,
}: VideoStorageWarningModalProps) {
  const handleConfirm = () => {
    onConfirm();
    onOpenChange(false);
  };

  const handleCancel = () => {
    onCancel();
    onOpenChange(false);
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <HardDrive className="h-5 w-5 text-yellow-500" />
            Video Storage Uses Disk Space
          </AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-4">
              <p>
                Enabling video storage will download and save full motion clips from
                your Protect cameras. This provides complete video footage for review
                but uses significant disk space.
              </p>

              <div className="bg-muted p-3 rounded-md">
                <p className="font-medium mb-2">Estimated storage usage:</p>
                <ul className="space-y-1 text-sm">
                  <li className="flex items-center gap-2">
                    <span className="text-muted-foreground">Per video:</span>
                    <span>5-30 MB depending on duration</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-muted-foreground">10 events/day:</span>
                    <span>50-300 MB/day</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-muted-foreground">30-day retention:</span>
                    <span>1.5-9 GB total</span>
                  </li>
                </ul>
              </div>

              <div className="flex items-start gap-2 text-sm text-muted-foreground">
                <AlertTriangle className="h-4 w-4 mt-0.5 text-yellow-500 shrink-0" />
                <span>
                  Videos are stored separately from events and have their own
                  retention period. Monitor disk usage in Settings &gt; Storage.
                </span>
              </div>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={handleCancel}>Cancel</AlertDialogCancel>
          <AlertDialogAction onClick={handleConfirm}>
            Enable Video Storage
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
