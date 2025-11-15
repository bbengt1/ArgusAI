/**
 * Reusable confirmation dialog component
 */

'use client';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

interface ConfirmDialogProps {
  /**
   * Whether dialog is open
   */
  open: boolean;
  /**
   * Dialog title
   */
  title: string;
  /**
   * Dialog description/message
   */
  description: string;
  /**
   * Confirm button text (default: "Confirm")
   */
  confirmText?: string;
  /**
   * Cancel button text (default: "Cancel")
   */
  cancelText?: string;
  /**
   * Whether confirm action is destructive (shows red button)
   */
  destructive?: boolean;
  /**
   * Confirm button click handler
   */
  onConfirm: () => void;
  /**
   * Cancel button click handler
   */
  onCancel: () => void;
}

/**
 * Confirmation dialog for destructive actions
 */
export function ConfirmDialog({
  open,
  title,
  description,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  destructive = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onCancel()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            variant="outline"
            onClick={onCancel}
          >
            {cancelText}
          </Button>
          <Button
            variant={destructive ? 'destructive' : 'default'}
            onClick={onConfirm}
          >
            {confirmText}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
