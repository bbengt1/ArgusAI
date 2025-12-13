/**
 * Camera Accuracy Table Component
 * Story P4-5.3: Accuracy Dashboard
 *
 * Displays per-camera feedback statistics in a sortable table
 */

'use client';

import { useState, useMemo } from 'react';
import { ArrowUpDown, ArrowUp, ArrowDown, Camera } from 'lucide-react';

import type { ICameraFeedbackStats } from '@/types/event';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';

interface CameraAccuracyTableProps {
  feedbackByCamera: Record<string, ICameraFeedbackStats>;
}

type SortField = 'camera_name' | 'accuracy_rate' | 'helpful_count' | 'not_helpful_count' | 'total';
type SortDirection = 'asc' | 'desc';

// Accuracy color badge
const getAccuracyBadgeVariant = (rate: number): 'default' | 'secondary' | 'destructive' => {
  if (rate >= 80) return 'default'; // green
  if (rate >= 60) return 'secondary'; // yellow
  return 'destructive'; // red
};

const getAccuracyBadgeClass = (rate: number): string => {
  if (rate >= 80) return 'bg-green-100 text-green-800 hover:bg-green-100';
  if (rate >= 60) return 'bg-yellow-100 text-yellow-800 hover:bg-yellow-100';
  return 'bg-red-100 text-red-800 hover:bg-red-100';
};

export function CameraAccuracyTable({ feedbackByCamera }: CameraAccuracyTableProps) {
  const [sortField, setSortField] = useState<SortField>('accuracy_rate');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  // Convert to array and add total
  const cameraData = useMemo(() => {
    return Object.values(feedbackByCamera).map((camera) => ({
      ...camera,
      total: camera.helpful_count + camera.not_helpful_count,
    }));
  }, [feedbackByCamera]);

  // Sort data
  const sortedData = useMemo(() => {
    const sorted = [...cameraData].sort((a, b) => {
      let aVal: string | number = a[sortField];
      let bVal: string | number = b[sortField];

      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase();
        bVal = (bVal as string).toLowerCase();
        return sortDirection === 'asc'
          ? aVal.localeCompare(bVal as string)
          : (bVal as string).localeCompare(aVal);
      }

      return sortDirection === 'asc' ? aVal - (bVal as number) : (bVal as number) - aVal;
    });
    return sorted;
  }, [cameraData, sortField, sortDirection]);

  // Handle sort click
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  // Sort icon
  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <ArrowUpDown className="ml-2 h-4 w-4 text-muted-foreground" />;
    }
    return sortDirection === 'asc' ? (
      <ArrowUp className="ml-2 h-4 w-4" />
    ) : (
      <ArrowDown className="ml-2 h-4 w-4" />
    );
  };

  if (cameraData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Camera className="h-5 w-5" />
            Per-Camera Accuracy
          </CardTitle>
          <CardDescription>Accuracy breakdown by camera</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-center text-muted-foreground py-8">
            No per-camera data available yet
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Camera className="h-5 w-5" />
          Per-Camera Accuracy
        </CardTitle>
        <CardDescription>
          Click column headers to sort. Identifies cameras that may need attention.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>
                  <Button
                    variant="ghost"
                    onClick={() => handleSort('camera_name')}
                    className="flex items-center -ml-4"
                  >
                    Camera Name
                    <SortIcon field="camera_name" />
                  </Button>
                </TableHead>
                <TableHead className="text-center">
                  <Button
                    variant="ghost"
                    onClick={() => handleSort('accuracy_rate')}
                    className="flex items-center"
                  >
                    Accuracy
                    <SortIcon field="accuracy_rate" />
                  </Button>
                </TableHead>
                <TableHead className="text-center">
                  <Button
                    variant="ghost"
                    onClick={() => handleSort('helpful_count')}
                    className="flex items-center"
                  >
                    Helpful
                    <SortIcon field="helpful_count" />
                  </Button>
                </TableHead>
                <TableHead className="text-center">
                  <Button
                    variant="ghost"
                    onClick={() => handleSort('not_helpful_count')}
                    className="flex items-center"
                  >
                    Not Helpful
                    <SortIcon field="not_helpful_count" />
                  </Button>
                </TableHead>
                <TableHead className="text-center">
                  <Button
                    variant="ghost"
                    onClick={() => handleSort('total')}
                    className="flex items-center"
                  >
                    Total
                    <SortIcon field="total" />
                  </Button>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedData.map((camera) => (
                <TableRow key={camera.camera_id}>
                  <TableCell className="font-medium">{camera.camera_name}</TableCell>
                  <TableCell className="text-center">
                    <Badge className={getAccuracyBadgeClass(camera.accuracy_rate)}>
                      {camera.accuracy_rate.toFixed(1)}%
                    </Badge>
                  </TableCell>
                  <TableCell className="text-center text-green-600">
                    {camera.helpful_count}
                  </TableCell>
                  <TableCell className="text-center text-red-600">
                    {camera.not_helpful_count}
                  </TableCell>
                  <TableCell className="text-center text-muted-foreground">
                    {camera.total}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
