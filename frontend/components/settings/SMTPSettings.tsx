/**
 * SMTP Settings Component (Story P16-1.7)
 *
 * Features:
 * - SMTP configuration form for email sending
 * - Connection test button
 * - Password masking with configured indicator
 * - Support for TLS and STARTTLS
 */

'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Mail,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Eye,
  EyeOff,
  Info,
} from 'lucide-react';

import { apiClient } from '@/lib/api-client';
import { useUnsavedChangesWarning } from '@/hooks/useUnsavedChangesWarning';
import { UnsavedIndicator } from './UnsavedIndicator';
import type { SMTPSettingsUpdate } from '@/types/settings';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

// Validation schema
const smtpConfigSchema = z.object({
  host: z.string().min(1, 'SMTP host is required').max(255),
  port: z.coerce.number().int().min(1, 'Port must be between 1-65535').max(65535, 'Port must be between 1-65535'),
  username: z.string().max(255).optional().or(z.literal('')),
  password: z.string().max(500).optional().or(z.literal('')),
  from_email: z.string().email('Valid email required').or(z.literal('')),
  from_name: z.string().max(100).optional().or(z.literal('')),
  use_tls: z.boolean(),
  use_starttls: z.boolean(),
  enabled: z.boolean(),
});

interface SMTPFormData {
  host: string;
  port: number;
  username?: string;
  password?: string;
  from_email: string;
  from_name: string;
  use_tls: boolean;
  use_starttls: boolean;
  enabled: boolean;
}

export function SMTPSettings() {
  const queryClient = useQueryClient();
  const [showPassword, setShowPassword] = useState(false);
  const [isTesting, setIsTesting] = useState(false);

  // Fetch SMTP configuration
  const configQuery = useQuery({
    queryKey: ['smtp-config'],
    queryFn: () => apiClient.smtp.getSettings(),
  });

  // Form setup
  const form = useForm<SMTPFormData>({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    resolver: zodResolver(smtpConfigSchema) as any,
    defaultValues: {
      host: '',
      port: 587,
      username: '',
      password: '',
      from_email: '',
      from_name: 'ArgusAI',
      use_tls: false,
      use_starttls: true,
      enabled: false,
    },
  });

  const { formState: { errors, isDirty } } = form;

  // Navigation warning when form is dirty
  useUnsavedChangesWarning({ isDirty });

  // Update form when config loads
  useEffect(() => {
    if (configQuery.data) {
      const config = configQuery.data;
      form.reset({
        host: config.host || '',
        port: config.port,
        username: config.username || '',
        password: '', // Never prefill password
        from_email: config.from_email || '',
        from_name: config.from_name || 'ArgusAI',
        use_tls: config.use_tls,
        use_starttls: config.use_starttls,
        enabled: config.enabled,
      });
    }
  }, [configQuery.data, form]);

  // Save mutation
  const saveMutation = useMutation({
    mutationFn: (data: SMTPSettingsUpdate) => apiClient.smtp.updateSettings(data),
    onSuccess: () => {
      toast.success('SMTP configuration saved', {
        description: 'Email settings updated successfully.',
      });
      queryClient.invalidateQueries({ queryKey: ['smtp-config'] });
    },
    onError: (error: Error) => {
      toast.error('Failed to save configuration', {
        description: error.message,
      });
    },
  });

  // Test connection handler
  const handleTestConnection = async () => {
    if (!form.getValues('host')) {
      toast.error('Enter SMTP host first');
      return;
    }

    setIsTesting(true);
    try {
      const result = await apiClient.smtp.testConnection();
      if (result.success) {
        toast.success('Connection successful', {
          description: result.message,
        });
      } else {
        toast.error('Connection failed', {
          description: result.message,
        });
      }
    } catch (error) {
      toast.error('Test failed', {
        description: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setIsTesting(false);
    }
  };

  // Save handler
  const handleSave = async (data: SMTPFormData) => {
    // Only send password if it was changed (not empty)
    const configUpdate: SMTPSettingsUpdate = {
      ...data,
      password: data.password || undefined,
    };
    saveMutation.mutate(configUpdate);
  };

  // Status badge
  const getStatusBadge = () => {
    if (!form.watch('enabled')) {
      return (
        <Badge variant="secondary">
          <Mail className="mr-1 h-3 w-3" />
          Disabled
        </Badge>
      );
    }

    if (configQuery.data?.host) {
      return (
        <Badge variant="default" className="bg-green-600">
          <CheckCircle2 className="mr-1 h-3 w-3" />
          Configured
        </Badge>
      );
    }

    return (
      <Badge variant="destructive">
        <AlertTriangle className="mr-1 h-3 w-3" />
        Not Configured
      </Badge>
    );
  };

  if (configQuery.isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <CardTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5" />
              Email / SMTP Settings
              <UnsavedIndicator isDirty={isDirty} />
            </CardTitle>
            <CardDescription>
              Configure SMTP server for sending invitation emails to new users
            </CardDescription>
          </div>
          {getStatusBadge()}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-6">
          {/* Master Enable Toggle */}
          <div className="flex items-center justify-between rounded-lg border p-4">
            <div className="space-y-0.5">
              <Label htmlFor="smtp-enabled" className="text-base font-medium">
                Enable Email Sending
              </Label>
              <p className="text-sm text-muted-foreground">
                Send invitation emails to new users with temporary login credentials
              </p>
            </div>
            <Switch
              id="smtp-enabled"
              checked={form.watch('enabled')}
              onCheckedChange={(checked) => form.setValue('enabled', checked, { shouldDirty: true })}
            />
          </div>

          {/* Collapsible Configuration Sections */}
          <div
            className={`grid transition-all duration-300 ease-in-out ${
              form.watch('enabled')
                ? 'grid-rows-[1fr] opacity-100'
                : 'grid-rows-[0fr] opacity-0'
            }`}
          >
            <div className="overflow-hidden">
              <div className="space-y-6">
                {/* SMTP Server Configuration */}
                <div className="space-y-4">
                  <h4 className="font-medium">SMTP Server</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="md:col-span-2 space-y-2">
                      <Label htmlFor="host">SMTP Host</Label>
                      <Input
                        id="host"
                        placeholder="smtp.gmail.com or mail.example.com"
                        {...form.register('host')}
                      />
                      {errors.host && (
                        <p className="text-sm text-destructive">{errors.host.message}</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="port">Port</Label>
                      <Input
                        id="port"
                        type="number"
                        placeholder="587"
                        {...form.register('port')}
                      />
                      {errors.port && (
                        <p className="text-sm text-destructive">{errors.port.message}</p>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="username">Username</Label>
                      <Input
                        id="username"
                        placeholder="your-email@example.com"
                        autoComplete="username"
                        {...form.register('username')}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label htmlFor="password">Password</Label>
                        {configQuery.data?.has_password && !form.watch('password') && (
                          <Badge variant="secondary" className="text-xs">
                            <CheckCircle2 className="mr-1 h-3 w-3" />
                            Configured
                          </Badge>
                        )}
                      </div>
                      <div className="relative">
                        <Input
                          id="password"
                          type={showPassword ? 'text' : 'password'}
                          placeholder={configQuery.data?.has_password ? '••••••••' : 'Enter password or app password'}
                          autoComplete="current-password"
                          {...form.register('password')}
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                          onClick={() => setShowPassword(!showPassword)}
                        >
                          {showPassword ? (
                            <EyeOff className="h-4 w-4 text-muted-foreground" />
                          ) : (
                            <Eye className="h-4 w-4 text-muted-foreground" />
                          )}
                        </Button>
                      </div>
                      {configQuery.data?.has_password && (
                        <p className="text-xs text-muted-foreground">
                          Leave empty to keep existing password
                        </p>
                      )}
                    </div>
                  </div>

                  {/* TLS/STARTTLS Options */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="flex items-center justify-between rounded-lg border p-3">
                      <div className="space-y-0.5">
                        <Label htmlFor="use_tls">Use TLS (Implicit)</Label>
                        <p className="text-xs text-muted-foreground">
                          Direct TLS connection (port 465)
                        </p>
                      </div>
                      <Switch
                        id="use_tls"
                        checked={form.watch('use_tls')}
                        onCheckedChange={(checked) => {
                          form.setValue('use_tls', checked, { shouldDirty: true });
                          // If TLS is enabled, disable STARTTLS
                          if (checked) {
                            form.setValue('use_starttls', false, { shouldDirty: true });
                          }
                        }}
                      />
                    </div>
                    <div className="flex items-center justify-between rounded-lg border p-3">
                      <div className="space-y-0.5">
                        <Label htmlFor="use_starttls">Use STARTTLS</Label>
                        <p className="text-xs text-muted-foreground">
                          Upgrade connection (port 587)
                        </p>
                      </div>
                      <Switch
                        id="use_starttls"
                        checked={form.watch('use_starttls')}
                        onCheckedChange={(checked) => {
                          form.setValue('use_starttls', checked, { shouldDirty: true });
                          // If STARTTLS is enabled, disable TLS
                          if (checked) {
                            form.setValue('use_tls', false, { shouldDirty: true });
                          }
                        }}
                      />
                    </div>
                  </div>

                  {/* Test Connection Button */}
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleTestConnection}
                    disabled={isTesting || !form.watch('host') || !form.watch('enabled')}
                  >
                    {isTesting ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Testing...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="mr-2 h-4 w-4" />
                        Test Connection
                      </>
                    )}
                  </Button>
                </div>

                {/* Sender Information */}
                <div className="space-y-4">
                  <h4 className="font-medium">Sender Information</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="from_email">From Email</Label>
                      <Input
                        id="from_email"
                        type="email"
                        placeholder="noreply@example.com"
                        {...form.register('from_email')}
                      />
                      {errors.from_email && (
                        <p className="text-sm text-destructive">{errors.from_email.message}</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="from_name">From Name</Label>
                      <Input
                        id="from_name"
                        placeholder="ArgusAI"
                        {...form.register('from_name')}
                      />
                    </div>
                  </div>
                </div>

                {/* Info Alert */}
                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertTitle>Email Invitations</AlertTitle>
                  <AlertDescription>
                    When enabled, newly created users can receive an email with their temporary
                    login credentials. Gmail users should use an{' '}
                    <a
                      href="https://support.google.com/accounts/answer/185833"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary underline"
                    >
                      App Password
                    </a>{' '}
                    instead of their regular password.
                  </AlertDescription>
                </Alert>
              </div>
            </div>
          </div>

          {/* Save Button */}
          {(form.watch('enabled') || isDirty) && (
            <div className="flex justify-end gap-2">
              {isDirty && (
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => form.reset()}
                  disabled={saveMutation.isPending}
                >
                  Cancel
                </Button>
              )}
              <Button
                type="button"
                onClick={form.handleSubmit(handleSave)}
                disabled={saveMutation.isPending || !isDirty}
              >
                {saveMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  'Save Changes'
                )}
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
