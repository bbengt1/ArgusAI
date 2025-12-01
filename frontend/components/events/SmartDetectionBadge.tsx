/**
 * SmartDetectionBadge - displays the smart detection type for Protect events
 *
 * Shows color-coded pill badges for different detection types:
 * - Person: Blue
 * - Vehicle: Purple
 * - Package: Orange
 * - Animal: Green
 * - Motion: Gray
 *
 * Follows UX spec Section 10.5 for styling and icon selection.
 */

'use client';

import { User, Car, Package, PawPrint, Waves, Bell } from 'lucide-react';

export type SmartDetectionType = 'person' | 'vehicle' | 'package' | 'animal' | 'motion' | 'ring';

interface SmartDetectionBadgeProps {
  detectionType: SmartDetectionType;
}

const DETECTION_CONFIG: Record<
  SmartDetectionType,
  { icon: typeof User; label: string; bgClass: string; textClass: string }
> = {
  person: {
    icon: User,
    label: 'Person',
    bgClass: 'bg-blue-100',
    textClass: 'text-blue-800',
  },
  vehicle: {
    icon: Car,
    label: 'Vehicle',
    bgClass: 'bg-purple-100',
    textClass: 'text-purple-800',
  },
  package: {
    icon: Package,
    label: 'Package',
    bgClass: 'bg-orange-100',
    textClass: 'text-orange-800',
  },
  animal: {
    icon: PawPrint,
    label: 'Animal',
    bgClass: 'bg-green-100',
    textClass: 'text-green-800',
  },
  motion: {
    icon: Waves,
    label: 'Motion',
    bgClass: 'bg-gray-100',
    textClass: 'text-gray-800',
  },
  ring: {
    icon: Bell,
    label: 'Doorbell',
    bgClass: 'bg-cyan-100',
    textClass: 'text-cyan-800',
  },
};

export function SmartDetectionBadge({ detectionType }: SmartDetectionBadgeProps) {
  const config = DETECTION_CONFIG[detectionType];

  if (!config) {
    return null;
  }

  const Icon = config.icon;

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${config.bgClass} ${config.textClass}`}
    >
      <Icon className="h-3 w-3" aria-hidden="true" />
      {config.label}
      <span className="sr-only">Smart detection: {config.label}</span>
    </span>
  );
}
