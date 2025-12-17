/**
 * Audio Settings Section Component (Story P6-3.3)
 *
 * Provides UI controls for configuring audio capture and event detection:
 * - Toggle to enable/disable audio capture
 * - Checkbox group for audio event types to detect
 * - Slider for per-camera confidence threshold override
 *
 * Only shown for RTSP cameras (USB cameras don't support audio extraction).
 */

'use client';

import { UseFormReturn } from 'react-hook-form';
import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Slider } from '@/components/ui/slider';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { HelpCircle, Volume2 } from 'lucide-react';
import type { CameraFormValues } from '@/lib/validations/camera';

interface AudioSettingsSectionProps {
  /**
   * React Hook Form instance from parent CameraForm
   */
  form: UseFormReturn<CameraFormValues>;
}

/**
 * Audio event type definitions with descriptions
 */
const AUDIO_EVENT_TYPES = [
  {
    id: 'glass_break',
    label: 'Glass Break',
    description: 'Sound of glass shattering or breaking',
  },
  {
    id: 'gunshot',
    label: 'Gunshot',
    description: 'Sound of gunfire or explosions',
  },
  {
    id: 'scream',
    label: 'Scream',
    description: 'Human screaming, shouting, or distress calls',
  },
  {
    id: 'doorbell',
    label: 'Doorbell',
    description: 'Doorbell ring or chime sounds',
  },
] as const;

/**
 * Audio Settings Section Component
 * Integrates with CameraForm to provide audio detection configuration UI
 */
export function AudioSettingsSection({ form }: AudioSettingsSectionProps) {
  const audioEnabled = form.watch('audio_enabled');

  return (
    <div className="space-y-6 border rounded-lg p-6 bg-muted/20">
      <div className="flex items-center gap-2">
        <Volume2 className="h-5 w-5 text-blue-600" aria-hidden="true" />
        <div>
          <h3 className="text-lg font-semibold mb-1">Audio Detection Settings</h3>
          <p className="text-sm text-muted-foreground">
            Configure audio capture and event detection for this camera
          </p>
        </div>
      </div>

      {/* Audio Enabled Toggle */}
      <FormField
        control={form.control}
        name="audio_enabled"
        render={({ field }) => (
          <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
            <div className="space-y-0.5">
              <FormLabel className="text-base">
                Enable Audio Capture
              </FormLabel>
              <FormDescription>
                Extract and analyze audio from this camera&apos;s RTSP stream
              </FormDescription>
            </div>
            <FormControl>
              <button
                type="button"
                role="switch"
                aria-checked={field.value ?? false}
                onClick={() => field.onChange(!field.value)}
                className={`
                  relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50
                  ${field.value ? 'bg-blue-600' : 'bg-gray-300'}
                `}
              >
                <span
                  className={`
                    inline-block h-5 w-5 transform rounded-full bg-white transition-transform
                    ${field.value ? 'translate-x-6' : 'translate-x-0.5'}
                  `}
                />
              </button>
            </FormControl>
          </FormItem>
        )}
      />

      {/* Audio Event Types - only show when audio is enabled */}
      {audioEnabled && (
        <>
          <FormField
            control={form.control}
            name="audio_event_types"
            render={() => (
              <FormItem>
                <div className="mb-4">
                  <FormLabel className="flex items-center gap-2">
                    Audio Event Types
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help" />
                        </TooltipTrigger>
                        <TooltipContent className="max-w-xs">
                          <p className="text-sm">
                            Select which types of audio events to detect.
                            Leave all unchecked to detect all types.
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </FormLabel>
                  <FormDescription>
                    Choose which sound events to detect on this camera
                  </FormDescription>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  {AUDIO_EVENT_TYPES.map((type) => (
                    <FormField
                      key={type.id}
                      control={form.control}
                      name="audio_event_types"
                      render={({ field }) => {
                        const currentValue = field.value ?? [];
                        return (
                          <FormItem
                            key={type.id}
                            className="flex flex-row items-start space-x-3 space-y-0 rounded-lg border p-3"
                          >
                            <FormControl>
                              <Checkbox
                                checked={currentValue.includes(type.id)}
                                onCheckedChange={(checked) => {
                                  if (checked) {
                                    field.onChange([...currentValue, type.id]);
                                  } else {
                                    field.onChange(
                                      currentValue.filter((value: string) => value !== type.id)
                                    );
                                  }
                                }}
                              />
                            </FormControl>
                            <div className="space-y-1 leading-none">
                              <FormLabel className="cursor-pointer font-medium">
                                {type.label}
                              </FormLabel>
                              <p className="text-xs text-muted-foreground">
                                {type.description}
                              </p>
                            </div>
                          </FormItem>
                        );
                      }}
                    />
                  ))}
                </div>
                <FormMessage />
              </FormItem>
            )}
          />

          {/* Confidence Threshold Slider */}
          <FormField
            control={form.control}
            name="audio_threshold"
            render={({ field }) => {
              const thresholdValue = field.value ?? null;
              const displayValue = thresholdValue !== null ? Math.round(thresholdValue * 100) : null;

              return (
                <FormItem>
                  <FormLabel className="flex items-center gap-2">
                    Confidence Threshold
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help" />
                        </TooltipTrigger>
                        <TooltipContent className="max-w-xs">
                          <p className="text-sm">
                            Minimum confidence score required for audio detections.
                            Higher values reduce false positives but may miss some events.
                            Set to &quot;Use Global Default&quot; to use system-wide threshold.
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </FormLabel>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">
                        {displayValue !== null ? `${displayValue}%` : 'Use Global Default (70%)'}
                      </span>
                      {thresholdValue !== null && (
                        <button
                          type="button"
                          onClick={() => field.onChange(null)}
                          className="text-xs text-blue-600 hover:underline"
                        >
                          Reset to Default
                        </button>
                      )}
                    </div>
                    <FormControl>
                      <Slider
                        min={0}
                        max={100}
                        step={5}
                        value={[displayValue ?? 70]}
                        onValueChange={(values) => {
                          field.onChange(values[0] / 100);
                        }}
                        className="w-full"
                      />
                    </FormControl>
                  </div>
                  <FormDescription>
                    Override the global confidence threshold for this camera (50-100% recommended)
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              );
            }}
          />
        </>
      )}
    </div>
  );
}
