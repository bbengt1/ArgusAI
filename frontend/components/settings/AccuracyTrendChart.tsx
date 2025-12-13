/**
 * Accuracy Trend Chart Component
 * Story P4-5.3: Accuracy Dashboard
 *
 * Displays daily feedback trend as a line chart using recharts
 */

'use client';

import { useMemo } from 'react';
import { format, parseISO } from 'date-fns';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { TrendingUp } from 'lucide-react';

import type { IDailyFeedbackStats } from '@/types/event';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface AccuracyTrendChartProps {
  dailyTrend: IDailyFeedbackStats[];
}

// Chart-compatible data type
interface ChartDataPoint {
  [key: string]: string | number;
}

// Custom tooltip component
interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ value: number; name: string; color: string }>;
  label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload || !label) {
    return null;
  }

  const helpful = payload.find((p) => p.name === 'Helpful')?.value || 0;
  const notHelpful = payload.find((p) => p.name === 'Not Helpful')?.value || 0;
  const total = helpful + notHelpful;
  const accuracyRate = total > 0 ? ((helpful / total) * 100).toFixed(1) : '0.0';

  return (
    <div className="bg-background border rounded-lg p-3 shadow-lg">
      <p className="font-medium text-sm mb-2">{format(parseISO(label), 'MMM d, yyyy')}</p>
      <div className="space-y-1 text-sm">
        <p className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-green-500" />
          <span className="text-muted-foreground">Helpful:</span>
          <span className="font-medium">{helpful}</span>
        </p>
        <p className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-red-400" />
          <span className="text-muted-foreground">Not Helpful:</span>
          <span className="font-medium">{notHelpful}</span>
        </p>
        <p className="flex items-center gap-2 pt-1 border-t">
          <span className="text-muted-foreground">Accuracy:</span>
          <span className="font-medium">{accuracyRate}%</span>
        </p>
      </div>
    </div>
  );
}

export function AccuracyTrendChart({ dailyTrend }: AccuracyTrendChartProps) {
  // Transform data for chart
  const chartData: ChartDataPoint[] = useMemo(() => {
    return dailyTrend.map((day) => ({
      date: day.date,
      displayDate: format(parseISO(day.date), 'MMM d'),
      Helpful: day.helpful_count,
      'Not Helpful': day.not_helpful_count,
    }));
  }, [dailyTrend]);

  if (dailyTrend.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Daily Trend
          </CardTitle>
          <CardDescription>Feedback over time</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-center text-muted-foreground py-12">
            No trend data available yet
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          Daily Trend
        </CardTitle>
        <CardDescription>Helpful vs not helpful feedback over time</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={chartData}
              margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
            >
              <defs>
                <linearGradient id="colorHelpful" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0.1} />
                </linearGradient>
                <linearGradient id="colorNotHelpful" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="displayDate"
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                allowDecimals={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                verticalAlign="top"
                height={36}
                formatter={(value) => <span className="text-sm">{value}</span>}
              />
              <Area
                type="monotone"
                dataKey="Helpful"
                stroke="#22c55e"
                fillOpacity={1}
                fill="url(#colorHelpful)"
                stackId="1"
              />
              <Area
                type="monotone"
                dataKey="Not Helpful"
                stroke="#ef4444"
                fillOpacity={1}
                fill="url(#colorNotHelpful)"
                stackId="1"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
