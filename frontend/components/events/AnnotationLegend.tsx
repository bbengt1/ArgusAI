/**
 * AnnotationLegend component - displays color-coded legend for AI bounding box annotations
 *
 * Story P15-5.5: Annotation Legend and Styling
 *
 * Shows entity type colors matching the backend FrameAnnotationService color palette.
 */

'use client';

import { useMemo } from 'react';

// Entity type colors matching backend/app/services/frame_annotation_service.py
const ENTITY_COLORS: Record<string, { hex: string; label: string }> = {
  person: { hex: '#3B82F6', label: 'Person' },     // Blue
  vehicle: { hex: '#22C55E', label: 'Vehicle' },   // Green
  package: { hex: '#F97316', label: 'Package' },   // Orange
  animal: { hex: '#A855F7', label: 'Animal' },     // Purple
  other: { hex: '#9CA3AF', label: 'Other' },       // Gray
};

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
  entity_type: string;
  confidence: number;
  label: string;
}

interface AnnotationLegendProps {
  boundingBoxes: BoundingBox[];
  compact?: boolean;
}

export function AnnotationLegend({ boundingBoxes, compact = false }: AnnotationLegendProps) {
  // Get unique entity types from bounding boxes
  const uniqueEntityTypes = useMemo(() => {
    const types = new Set<string>();
    boundingBoxes.forEach((box) => {
      types.add(box.entity_type.toLowerCase());
    });
    return Array.from(types);
  }, [boundingBoxes]);

  // Count entities by type
  const entityCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    boundingBoxes.forEach((box) => {
      const type = box.entity_type.toLowerCase();
      counts[type] = (counts[type] || 0) + 1;
    });
    return counts;
  }, [boundingBoxes]);

  if (uniqueEntityTypes.length === 0) {
    return null;
  }

  return (
    <div className="bg-black/70 backdrop-blur-sm rounded-lg px-3 py-2 text-white">
      <div className={`flex ${compact ? 'flex-row gap-3' : 'flex-col gap-1.5'}`}>
        {uniqueEntityTypes.map((entityType) => {
          const colorInfo = ENTITY_COLORS[entityType] || ENTITY_COLORS.other;
          const count = entityCounts[entityType] || 0;

          return (
            <div key={entityType} className="flex items-center gap-2">
              {/* Color swatch */}
              <div
                className="w-3 h-3 rounded-sm border border-white/30"
                style={{ backgroundColor: colorInfo.hex }}
              />

              {/* Label and count */}
              <span className="text-xs font-medium">
                {colorInfo.label}
                {count > 1 && (
                  <span className="text-white/70 ml-1">({count})</span>
                )}
              </span>
            </div>
          );
        })}
      </div>

      {/* Total count */}
      {!compact && boundingBoxes.length > 1 && (
        <div className="mt-1.5 pt-1.5 border-t border-white/20 text-xs text-white/70">
          {boundingBoxes.length} objects detected
        </div>
      )}
    </div>
  );
}
