/**
 * Zod validation schemas for camera forms
 */

import { z } from 'zod';

/**
 * Detection zone vertex schema
 * Coordinates normalized to 0-1 scale
 */
export const zoneVertexSchema = z.object({
  x: z.number().min(0).max(1),
  y: z.number().min(0).max(1),
});

/**
 * Detection zone polygon schema
 * Validates minimum 3 vertices, coordinate bounds, required fields
 */
export const detectionZoneSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1).max(100),
  vertices: z.array(zoneVertexSchema).min(3, 'Polygon must have at least 3 vertices'),
  enabled: z.boolean(),
});

/**
 * Detection schedule schema
 * Validates time format, days array, and overnight schedule support
 */
export const detectionScheduleSchema = z.object({
  enabled: z.boolean(),
  start_time: z.string().regex(/^\d{2}:\d{2}$/, 'Start time must be in HH:MM format'),
  end_time: z.string().regex(/^\d{2}:\d{2}$/, 'End time must be in HH:MM format'),
  days: z.array(z.number().int().min(0).max(6)).min(1, 'At least one day must be selected'),
});

/**
 * Camera form schema with conditional validation
 * Mirrors backend Pydantic validation rules
 */
export const cameraFormSchema = z.object({
  name: z
    .string()
    .min(1, 'Camera name is required')
    .max(100, 'Camera name must be 100 characters or less'),

  type: z.enum(['rtsp', 'usb']),

  // RTSP fields (conditional)
  rtsp_url: z.string().optional().nullable(),
  username: z.string().max(100).optional().nullable(),
  password: z.string().max(100).optional().nullable(),

  // USB fields (conditional)
  device_index: z.number().int().min(0).optional().nullable(),

  // Common fields (with defaults in defaultValues, not Zod schema)
  frame_rate: z.number().int().min(1).max(30),
  is_enabled: z.boolean(),
  motion_enabled: z.boolean(),
  motion_sensitivity: z.enum(['low', 'medium', 'high']),
  motion_cooldown: z.number().int().min(5).max(300),
  motion_algorithm: z.enum(['mog2', 'knn', 'frame_diff']),
  detection_zones: z.array(detectionZoneSchema).max(10, 'Maximum 10 zones per camera').optional(),
  detection_schedule: detectionScheduleSchema.optional().nullable(),
  // Phase 3: AI analysis mode
  analysis_mode: z.enum(['single_frame', 'multi_frame', 'video_native']),
}).superRefine((data, ctx) => {
  // Validate RTSP-specific fields
  if (data.type === 'rtsp') {
    if (!data.rtsp_url) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'RTSP URL is required for RTSP cameras',
        path: ['rtsp_url'],
      });
    } else if (!data.rtsp_url.startsWith('rtsp://') && !data.rtsp_url.startsWith('rtsps://')) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'RTSP URL must start with rtsp:// or rtsps://',
        path: ['rtsp_url'],
      });
    }
  }

  // Validate USB-specific fields
  if (data.type === 'usb') {
    if (data.device_index === undefined || data.device_index === null) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Device index is required for USB cameras',
        path: ['device_index'],
      });
    }
  }
});

export type CameraFormValues = z.infer<typeof cameraFormSchema>;
