/**
 * Camera list page
 * Displays grid of cameras with add/edit/delete actions
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Video, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useCameras } from '@/hooks/useCameras';
import { useToast } from '@/hooks/useToast';
import { CameraPreview } from '@/components/cameras/CameraPreview';
import { EmptyState } from '@/components/common/EmptyState';
import { Loading } from '@/components/common/Loading';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { apiClient } from '@/lib/api-client';
import type { ICamera } from '@/types/camera';

/**
 * Cameras page component
 */
export default function CamerasPage() {
  const router = useRouter();
  const { cameras, loading, error, refresh } = useCameras();
  const { showSuccess, showError } = useToast();

  // Delete confirmation state
  const [deleteDialog, setDeleteDialog] = useState<{
    open: boolean;
    camera: ICamera | null;
  }>({ open: false, camera: null });

  /**
   * Handle delete camera click
   */
  const handleDeleteClick = (camera: ICamera) => {
    setDeleteDialog({ open: true, camera });
  };

  /**
   * Confirm delete camera
   */
  const handleConfirmDelete = async () => {
    if (!deleteDialog.camera) return;

    try {
      await apiClient.cameras.delete(deleteDialog.camera.id);
      showSuccess('Camera deleted successfully');
      setDeleteDialog({ open: false, camera: null });
      refresh();
    } catch (err) {
      showError(err instanceof Error ? err.message : 'Failed to delete camera');
    }
  };

  /**
   * Cancel delete
   */
  const handleCancelDelete = () => {
    setDeleteDialog({ open: false, camera: null });
  };

  /**
   * Navigate to add camera page
   */
  const handleAddCamera = () => {
    router.push('/cameras/new');
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Page header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Cameras</h1>
          <p className="text-muted-foreground mt-2">
            Manage your camera feeds and configurations
          </p>
        </div>
        <Button onClick={handleAddCamera}>
          <Plus className="h-4 w-4 mr-2" />
          Add Camera
        </Button>
      </div>

      {/* Loading state */}
      {loading && <Loading message="Loading cameras..." />}

      {/* Error state */}
      {error && !loading && (
        <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-lg">
          <p className="font-medium">Error loading cameras</p>
          <p className="text-sm mt-1">{error}</p>
          <Button
            variant="outline"
            size="sm"
            onClick={refresh}
            className="mt-3"
          >
            Retry
          </Button>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && cameras.length === 0 && (
        <EmptyState
          icon={<Video className="h-16 w-16" />}
          title="No cameras configured yet"
          description="Add your first camera to start monitoring your space with AI-powered event detection."
          action={{
            label: 'Add Camera',
            onClick: handleAddCamera,
          }}
        />
      )}

      {/* Camera grid */}
      {!loading && !error && cameras.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {cameras.map((camera) => (
            <CameraPreview
              key={camera.id}
              camera={camera}
              onDelete={handleDeleteClick}
            />
          ))}
        </div>
      )}

      {/* Delete confirmation dialog */}
      <ConfirmDialog
        open={deleteDialog.open}
        title="Delete Camera"
        description={`Are you sure? This will delete all events from this camera.`}
        confirmText="Delete"
        cancelText="Cancel"
        destructive
        onConfirm={handleConfirmDelete}
        onCancel={handleCancelDelete}
      />
    </div>
  );
}
