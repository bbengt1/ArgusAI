/**
 * Forced Password Change Page (Story P15-2.6)
 *
 * Displayed when a user has must_change_password=true
 * For temporary passwords, current password is not required.
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { Eye, EyeOff, Loader2, Lock, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';
import Image from 'next/image';

import { apiClient } from '@/lib/api-client';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';

// Password validation schema - current password optional for forced change
const passwordChangeSchema = z.object({
  newPassword: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least 1 uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least 1 lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least 1 number')
    .regex(/[^A-Za-z0-9]/, 'Password must contain at least 1 special character'),
  confirmPassword: z.string().min(1, 'Please confirm your new password'),
}).refine(data => data.newPassword === data.confirmPassword, {
  message: 'Passwords do not match',
  path: ['confirmPassword'],
});

type PasswordChangeFormData = z.infer<typeof passwordChangeSchema>;

// Password strength requirements for visual feedback
const passwordRequirements = [
  { regex: /.{8,}/, label: 'At least 8 characters' },
  { regex: /[A-Z]/, label: 'At least 1 uppercase letter' },
  { regex: /[a-z]/, label: 'At least 1 lowercase letter' },
  { regex: /[0-9]/, label: 'At least 1 number' },
  { regex: /[^A-Za-z0-9]/, label: 'At least 1 special character' },
];

export default function ChangePasswordPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, checkAuth } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Redirect if not authenticated or doesn't need password change
  useEffect(() => {
    if (!authLoading) {
      if (!isAuthenticated) {
        router.push('/login');
      } else if (user && !user.must_change_password) {
        // Already changed password or doesn't need to
        router.push('/');
      }
    }
  }, [isAuthenticated, authLoading, user, router]);

  const form = useForm<PasswordChangeFormData>({
    resolver: zodResolver(passwordChangeSchema),
    defaultValues: {
      newPassword: '',
      confirmPassword: '',
    },
  });

  const { register, handleSubmit, formState: { errors }, watch } = form;
  const newPassword = watch('newPassword');

  const onSubmit = async (data: PasswordChangeFormData) => {
    try {
      setIsSubmitting(true);
      // For forced password change, current_password is optional
      await apiClient.auth.changePassword({
        new_password: data.newPassword,
      });
      toast.success('Password changed successfully');
      // Refresh auth state to get updated must_change_password flag
      await checkAuth();
      router.push('/');
    } catch (error) {
      if (error instanceof Error) {
        toast.error(error.message || 'Failed to change password');
      } else {
        toast.error('Failed to change password. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Show loading while checking auth
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  // Don't render if not authenticated or doesn't need change
  if (!isAuthenticated || !user?.must_change_password) {
    return null;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center mb-4">
            <Image
              src="/icons/icon-96.png"
              alt="ArgusAI"
              width={64}
              height={64}
              className="rounded-xl"
              priority
            />
          </div>
          <div className="flex items-center justify-center gap-2">
            <Lock className="h-5 w-5 text-amber-500" />
            <CardTitle className="text-2xl font-bold">
              Change Your Password
            </CardTitle>
          </div>
          <CardDescription>
            You must set a new password before continuing
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Alert className="mb-4">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Your account requires a password change. Please create a secure password to continue.
            </AlertDescription>
          </Alert>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* New Password */}
            <div className="space-y-2">
              <Label htmlFor="newPassword">New Password</Label>
              <div className="relative">
                <Input
                  id="newPassword"
                  type={showNewPassword ? 'text' : 'password'}
                  placeholder="Enter your new password"
                  autoComplete="new-password"
                  disabled={isSubmitting}
                  {...register('newPassword')}
                  className={errors.newPassword ? 'border-destructive' : ''}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  aria-label={showNewPassword ? 'Hide new password' : 'Show new password'}
                >
                  {showNewPassword ? (
                    <EyeOff className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <Eye className="h-4 w-4 text-muted-foreground" />
                  )}
                </Button>
              </div>
              {errors.newPassword && (
                <p className="text-sm text-destructive">{errors.newPassword.message}</p>
              )}

              {/* Password Strength Indicator */}
              {newPassword && (
                <div className="mt-2 space-y-1">
                  <p className="text-xs text-muted-foreground font-medium">Password requirements:</p>
                  <ul className="text-xs space-y-1">
                    {passwordRequirements.map((req, index) => {
                      const met = req.regex.test(newPassword);
                      return (
                        <li key={index} className={`flex items-center gap-1 ${met ? 'text-green-600' : 'text-muted-foreground'}`}>
                          {met ? (
                            <CheckCircle2 className="h-3 w-3" />
                          ) : (
                            <XCircle className="h-3 w-3" />
                          )}
                          {req.label}
                        </li>
                      );
                    })}
                  </ul>
                </div>
              )}
            </div>

            {/* Confirm New Password */}
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm New Password</Label>
              <div className="relative">
                <Input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  placeholder="Confirm your new password"
                  autoComplete="new-password"
                  disabled={isSubmitting}
                  {...register('confirmPassword')}
                  className={errors.confirmPassword ? 'border-destructive' : ''}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <Eye className="h-4 w-4 text-muted-foreground" />
                  )}
                </Button>
              </div>
              {errors.confirmPassword && (
                <p className="text-sm text-destructive">{errors.confirmPassword.message}</p>
              )}
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={isSubmitting}
              className="w-full"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Changing Password...
                </>
              ) : (
                'Set New Password'
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
