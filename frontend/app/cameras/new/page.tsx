/**
 * Add new camera page
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { CameraForm } from '@/components/cameras/CameraForm';
import { useToast } from '@/hooks/useToast';
import { apiClient, ApiError } from '@/lib/api-client';
import type { CameraFormValues } from '@/lib/validations/camera';

/**
 * New camera page component
 */
export default function NewCameraPage() {
  const router = useRouter();
  const { showSuccess, showError } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);

  /**
   * Handle form submission
   */
  const handleSubmit = async (data: CameraFormValues) => {
    setIsSubmitting(true);

    try {
      await apiClient.cameras.create(data);
      showSuccess('Camera added successfully');
      router.push('/cameras');
    } catch (err) {
      if (err instanceof ApiError) {
        showError(err.message);
      } else {
        showError('Failed to add camera');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Handle cancel
   */
  const handleCancel = () => {
    router.push('/cameras');
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      {/* Back button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={handleCancel}
        className="mb-6"
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to Cameras
      </Button>

      {/* Page header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Add Camera</h1>
        <p className="text-muted-foreground mt-2">
          Configure a new camera for event monitoring
        </p>
      </div>

      {/* Form */}
      <div className="bg-card border rounded-lg p-6">
        <CameraForm
          onSubmit={handleSubmit}
          onCancel={handleCancel}
          isSubmitting={isSubmitting}
        />
      </div>
    </div>
  );
}
