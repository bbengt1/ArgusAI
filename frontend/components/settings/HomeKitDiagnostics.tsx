'use client';

/**
 * HomeKitDiagnostics component (Story P7-1.1 AC6)
 *
 * Displays diagnostic information for HomeKit troubleshooting including:
 * - Bridge status and mDNS advertising state
 * - Network binding info
 * - Connected clients count
 * - Recent diagnostic logs with category filtering
 * - Warnings and errors prominently displayed
 */
import React, { useState } from 'react';
import {
  useHomekitDiagnostics,
  type HomekitDiagnosticEntry,
} from '@/hooks/useHomekitStatus';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Loader2,
  AlertCircle,
  Check,
  X,
  Radio,
  Network,
  Users,
  Activity,
  Clock,
  Filter,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

// Log level badge colors
const levelColors: Record<string, string> = {
  debug: 'bg-gray-500',
  info: 'bg-blue-500',
  warning: 'bg-yellow-500',
  error: 'bg-red-500',
};

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

interface DiagnosticLogEntryProps {
  entry: HomekitDiagnosticEntry;
}

function DiagnosticLogEntry({ entry }: DiagnosticLogEntryProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border-b border-border py-2 last:border-0">
      <div
        className="flex items-start justify-between gap-2 cursor-pointer"
        onClick={() => entry.details && setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-muted-foreground font-mono">
            {formatTimestamp(entry.timestamp)}
          </span>
          <Badge className={`${levelColors[entry.level]} text-white text-xs`}>
            {entry.level}
          </Badge>
          <Badge variant="outline" className={`text-xs`}>
            {entry.category}
          </Badge>
        </div>
        {entry.details && (
          <Button variant="ghost" size="sm" className="h-5 w-5 p-0">
            {expanded ? (
              <ChevronUp className="h-3 w-3" />
            ) : (
              <ChevronDown className="h-3 w-3" />
            )}
          </Button>
        )}
      </div>
      <p className="text-sm mt-1">{entry.message}</p>
      {expanded && entry.details && (
        <pre className="mt-2 p-2 bg-muted rounded text-xs overflow-x-auto">
          {JSON.stringify(entry.details, null, 2)}
        </pre>
      )}
    </div>
  );
}

interface HomeKitDiagnosticsProps {
  enabled?: boolean;
}

export function HomeKitDiagnostics({ enabled = true }: HomeKitDiagnosticsProps) {
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(
    new Set(['lifecycle', 'pairing', 'event', 'network', 'mdns'])
  );
  const [selectedLevels, setSelectedLevels] = useState<Set<string>>(
    new Set(['debug', 'info', 'warning', 'error'])
  );

  const { data: diagnostics, isLoading, error } = useHomekitDiagnostics({
    enabled,
    refetchInterval: 5000, // 5-second polling
  });

  const toggleCategory = (category: string) => {
    setSelectedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  };

  const toggleLevel = (level: string) => {
    setSelectedLevels((prev) => {
      const next = new Set(prev);
      if (next.has(level)) {
        next.delete(level);
      } else {
        next.add(level);
      }
      return next;
    });
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>
          Failed to load diagnostics. {(error as Error).message}
        </AlertDescription>
      </Alert>
    );
  }

  if (!diagnostics) {
    return null;
  }

  // Filter logs by selected categories and levels
  const filteredLogs = diagnostics.recent_logs.filter(
    (log) =>
      selectedCategories.has(log.category) && selectedLevels.has(log.level)
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          <CardTitle>Diagnostics</CardTitle>
        </div>
        <CardDescription>
          HomeKit bridge diagnostic information for troubleshooting
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Errors Alert */}
        {diagnostics.errors.length > 0 && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Errors ({diagnostics.errors.length})</AlertTitle>
            <AlertDescription>
              <ul className="list-disc list-inside mt-2">
                {diagnostics.errors.map((err, i) => (
                  <li key={i} className="text-sm">
                    {err}
                  </li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {/* Warnings Alert */}
        {diagnostics.warnings.length > 0 && (
          <Alert className="border-yellow-500">
            <AlertCircle className="h-4 w-4 text-yellow-500" />
            <AlertTitle className="text-yellow-500">
              Warnings ({diagnostics.warnings.length})
            </AlertTitle>
            <AlertDescription>
              <ul className="list-disc list-inside mt-2">
                {diagnostics.warnings.map((warn, i) => (
                  <li key={i} className="text-sm">
                    {warn}
                  </li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {/* Status Grid */}
        <div className="grid grid-cols-2 gap-4">
          {/* Bridge Status */}
          <div className="flex items-center gap-2">
            <div
              className={`w-3 h-3 rounded-full ${
                diagnostics.bridge_running ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <span className="text-sm">
              Bridge {diagnostics.bridge_running ? 'Running' : 'Stopped'}
            </span>
          </div>

          {/* mDNS Status */}
          <div className="flex items-center gap-2">
            <Radio
              className={`h-4 w-4 ${
                diagnostics.mdns_advertising
                  ? 'text-green-500'
                  : 'text-muted-foreground'
              }`}
            />
            <span className="text-sm">
              mDNS{' '}
              {diagnostics.mdns_advertising ? 'Advertising' : 'Not Advertising'}
            </span>
          </div>

          {/* Network Binding */}
          {diagnostics.network_binding && (
            <div className="flex items-center gap-2">
              <Network className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-mono">
                {diagnostics.network_binding.ip}:{diagnostics.network_binding.port}
              </span>
            </div>
          )}

          {/* Connected Clients */}
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">
              {diagnostics.connected_clients} Connected
            </span>
          </div>
        </div>

        {/* Last Event Delivery */}
        {diagnostics.last_event_delivery && (
          <div className="border rounded-lg p-3 bg-muted/30">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Last Event Delivery</span>
              {diagnostics.last_event_delivery.delivered ? (
                <Badge className="bg-green-500 text-white">
                  <Check className="h-3 w-3 mr-1" />
                  Delivered
                </Badge>
              ) : (
                <Badge variant="destructive">
                  <X className="h-3 w-3 mr-1" />
                  Failed
                </Badge>
              )}
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm text-muted-foreground">
              <span>Camera: {diagnostics.last_event_delivery.camera_id.slice(0, 8)}...</span>
              <span>Sensor: {diagnostics.last_event_delivery.sensor_type}</span>
              <span className="col-span-2">
                Time: {formatTimestamp(diagnostics.last_event_delivery.timestamp)}
              </span>
            </div>
          </div>
        )}

        {/* Log Filters */}
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Filters:</span>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm">
                Categories ({selectedCategories.size})
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuLabel>Categories</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {['lifecycle', 'pairing', 'event', 'network', 'mdns'].map((cat) => (
                <DropdownMenuCheckboxItem
                  key={cat}
                  checked={selectedCategories.has(cat)}
                  onCheckedChange={() => toggleCategory(cat)}
                >
                  {cat}
                </DropdownMenuCheckboxItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm">
                Levels ({selectedLevels.size})
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuLabel>Log Levels</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {['debug', 'info', 'warning', 'error'].map((level) => (
                <DropdownMenuCheckboxItem
                  key={level}
                  checked={selectedLevels.has(level)}
                  onCheckedChange={() => toggleLevel(level)}
                >
                  {level}
                </DropdownMenuCheckboxItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Diagnostic Logs */}
        <div className="border rounded-lg">
          <div className="px-3 py-2 border-b bg-muted/50">
            <span className="text-sm font-medium">
              Recent Logs ({filteredLogs.length})
            </span>
          </div>
          <ScrollArea className="h-64">
            <div className="px-3">
              {filteredLogs.length === 0 ? (
                <div className="py-8 text-center text-muted-foreground text-sm">
                  No logs matching filters
                </div>
              ) : (
                filteredLogs.map((log, i) => (
                  <DiagnosticLogEntry key={i} entry={log} />
                ))
              )}
            </div>
          </ScrollArea>
        </div>
      </CardContent>
    </Card>
  );
}
