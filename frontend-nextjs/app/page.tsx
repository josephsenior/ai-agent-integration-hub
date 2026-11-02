'use client';

import { useEffect, useState } from 'react';
import { Layout } from '@/components/layout';
import { ChatTab } from '@/components/chat-tab';
import { MessagesTab } from '@/components/messages-tab';
import { IntegrationsTab } from '@/components/integrations-tab';
import { AnalyticsTab } from '@/components/analytics-tab';
import { api } from '@/lib/api';
import { wsClient } from '@/lib/websocket';
import { LoginForm } from '@/components/login-form';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MessageSquare, Inbox, Plug, BarChart3 } from 'lucide-react';

export default function Home() {
  const [authenticated, setAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    api.currentUser().then(() => setAuthenticated(true)).catch(() => setAuthenticated(false));
  }, []);

  useEffect(() => {
    if (!authenticated) return;
    wsClient.connect();
    return () => wsClient.disconnect();
  }, [authenticated]);

  async function handleLogout() {
    await api.logout().catch(() => undefined);
    setAuthenticated(false);
  }

  if (authenticated === null) return <main className="min-h-screen grid place-items-center">Checking operator session…</main>;
  if (!authenticated) return <LoginForm onSuccess={() => setAuthenticated(true)} />;

  return (
    <Layout onLogout={handleLogout}>
      <div className="flex-1 space-y-8 p-8">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h1 className="text-5xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
              AI Agent Integration Hub
            </h1>
            <p className="text-muted-foreground text-lg mt-2">
              Unified platform for AI agent integrations across multiple channels
            </p>
          </div>
        </div>

        <Tabs defaultValue="chat" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="chat" className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Chat
            </TabsTrigger>
            <TabsTrigger value="messages" className="flex items-center gap-2">
              <Inbox className="h-4 w-4" />
              Messages
            </TabsTrigger>
            <TabsTrigger value="integrations" className="flex items-center gap-2">
              <Plug className="h-4 w-4" />
              Integrations
            </TabsTrigger>
            <TabsTrigger value="analytics" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Analytics
            </TabsTrigger>
          </TabsList>
          <TabsContent value="chat" className="mt-6">
            <ChatTab />
          </TabsContent>
          <TabsContent value="messages" className="mt-6">
            <MessagesTab />
          </TabsContent>
          <TabsContent value="integrations" className="mt-6">
            <IntegrationsTab />
          </TabsContent>
          <TabsContent value="analytics" className="mt-6">
            <AnalyticsTab />
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
}
