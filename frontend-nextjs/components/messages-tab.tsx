'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { RefreshCw, Filter } from 'lucide-react';
import { api } from '@/lib/api';
import type { Message, MessageChannel, MessageStatus } from '@/types';
import { formatDate } from '@/lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';

export function MessagesTab() {
  const [channelFilter, setChannelFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [limit, setLimit] = useState(50);

  const { data: messages, isLoading, refetch } = useQuery<Message[]>({
    queryKey: ['messages', channelFilter, statusFilter, limit],
    queryFn: () =>
      api.listMessages({
        channel: channelFilter !== 'all' ? channelFilter : undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        limit,
      }),
  });

  const channels: MessageChannel[] = ['api', 'slack', 'discord', 'email', 'webhook', 'websocket'];
  const statuses: MessageStatus[] = ['pending', 'processing', 'completed', 'failed', 'delivered'];

  return (
    <div className="space-y-4">
      {/* Filters Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
          <CardDescription>Filter messages by channel, status, or limit</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex-1 min-w-[200px]">
              <Select value={channelFilter} onValueChange={setChannelFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="All Channels" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Channels</SelectItem>
                  {channels.map((ch) => (
                    <SelectItem key={ch} value={ch}>
                      {ch.charAt(0).toUpperCase() + ch.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1 min-w-[200px]">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="All Statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  {statuses.map((st) => (
                    <SelectItem key={st} value={st}>
                      {st.charAt(0).toUpperCase() + st.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="w-32">
              <Input
                type="number"
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                min={1}
                max={100}
                placeholder="Limit"
              />
            </div>
            <Button onClick={() => refetch()} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Messages List Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Message History</CardTitle>
          <CardDescription>
            {messages ? `${messages.length} message${messages.length !== 1 ? 's' : ''} found` : 'Loading...'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="p-8 text-center text-muted-foreground">Loading messages...</div>
          ) : !messages || messages.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <p className="text-lg mb-2">No messages found</p>
              <p className="text-sm">Try adjusting your filters or send a message first</p>
            </div>
          ) : (
            <ScrollArea className="h-[600px]">
              <div className="space-y-4">
                {messages.map((message) => (
                  <Card key={message.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-2 flex-wrap">
                          <Badge variant="outline">{message.channel}</Badge>
                          <Badge
                            variant={
                              message.status === 'completed'
                                ? 'default'
                                : message.status === 'failed'
                                ? 'destructive'
                                : 'secondary'
                            }
                          >
                            {message.status}
                          </Badge>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {formatDate(message.created_at)}
                        </span>
                      </div>
                      <div className="space-y-3">
                        <div>
                          <p className="text-sm font-semibold mb-1">Message</p>
                          <p className="text-sm text-muted-foreground">{message.content}</p>
                        </div>
                        {message.response && (
                          <>
                            <Separator />
                            <div>
                              <p className="text-sm font-semibold mb-1">Response</p>
                              <p className="text-sm">{message.response}</p>
                            </div>
                          </>
                        )}
                        {message.user_id && (
                          <div className="pt-2">
                            <p className="text-xs text-muted-foreground">User ID: {message.user_id}</p>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
