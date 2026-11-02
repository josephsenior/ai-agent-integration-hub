'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Message } from '@/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Info } from 'lucide-react';

export function AnalyticsTab() {
  const { data: messages } = useQuery<Message[]>({
    queryKey: ['messages', 'all', 'all', 100],
    queryFn: () => api.listMessages({ limit: 100 }),
  });

  const stats = messages
    ? {
        totalMessages: messages.length,
        completed: messages.filter((m) => m.status === 'completed').length,
        failed: messages.filter((m) => m.status === 'failed').length,
        pending: messages.filter((m) => m.status === 'pending').length,
        byChannel: messages.reduce((acc, m) => {
          acc[m.channel] = (acc[m.channel] || 0) + 1;
          return acc;
        }, {} as Record<string, number>),
      }
    : null;

  return (
    <div className="space-y-6">
      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Messages</CardDescription>
            <CardTitle className="text-3xl">{stats?.totalMessages || 0}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Completed</CardDescription>
            <CardTitle className="text-3xl text-green-600">{stats?.completed || 0}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Failed</CardDescription>
            <CardTitle className="text-3xl text-red-600">{stats?.failed || 0}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Pending</CardDescription>
            <CardTitle className="text-3xl text-yellow-600">{stats?.pending || 0}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Channel Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Messages by Channel</CardTitle>
          <CardDescription>Distribution of messages across different channels</CardDescription>
        </CardHeader>
        <CardContent>
          {stats?.byChannel ? (
            <div className="space-y-4">
              {Object.entries(stats.byChannel).map(([channel, count]) => (
                <div key={channel} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium capitalize">{channel}</span>
                    <span className="text-muted-foreground">{count} messages</span>
                  </div>
                  <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all"
                      style={{
                        width: `${(count / (stats.totalMessages || 1)) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-8">No data available</p>
          )}
        </CardContent>
      </Card>

      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          Analytics dashboard is in development. More detailed metrics and charts coming soon!
        </AlertDescription>
      </Alert>
    </div>
  );
}
