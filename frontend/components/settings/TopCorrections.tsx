/**
 * Top Corrections Component
 * Story P4-5.3: Accuracy Dashboard
 *
 * Displays a list of common correction patterns from user feedback
 */

'use client';

import { MessageSquare, AlertCircle } from 'lucide-react';

import type { ICorrectionSummary } from '@/types/event';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface TopCorrectionsProps {
  corrections: ICorrectionSummary[];
}

export function TopCorrections({ corrections }: TopCorrectionsProps) {
  if (corrections.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Top Corrections
          </CardTitle>
          <CardDescription>Common feedback patterns</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <AlertCircle className="h-8 w-8 text-muted-foreground mb-2" />
            <p className="text-muted-foreground">No corrections recorded</p>
            <p className="text-xs text-muted-foreground mt-1">
              Corrections appear when users mark descriptions as not helpful and provide details
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Limit to top 10
  const topCorrections = corrections.slice(0, 10);

  // Max count for relative sizing
  const maxCount = Math.max(...topCorrections.map((c) => c.count));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          Top Corrections
        </CardTitle>
        <CardDescription>
          Common patterns in user feedback ({corrections.length} unique corrections)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="space-y-3">
          {topCorrections.map((correction, index) => {
            const isLongText = correction.correction_text.length > 60;
            const displayText = isLongText
              ? `${correction.correction_text.substring(0, 60)}...`
              : correction.correction_text;

            // Calculate bar width as percentage of max
            const barWidth = (correction.count / maxCount) * 100;

            return (
              <li key={index} className="relative">
                {/* Background bar */}
                <div
                  className="absolute inset-0 bg-muted rounded-md"
                  style={{ width: `${barWidth}%` }}
                />

                <div className="relative flex items-center justify-between p-2 min-h-[40px]">
                  {isLongText ? (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <span className="text-sm flex-1 mr-2 cursor-help">
                          {displayText}
                        </span>
                      </TooltipTrigger>
                      <TooltipContent side="bottom" className="max-w-md">
                        <p>{correction.correction_text}</p>
                      </TooltipContent>
                    </Tooltip>
                  ) : (
                    <span className="text-sm flex-1 mr-2">{displayText}</span>
                  )}
                  <Badge variant="secondary" className="shrink-0">
                    {correction.count}x
                  </Badge>
                </div>
              </li>
            );
          })}
        </ul>
      </CardContent>
    </Card>
  );
}
