'use client';

import { useEffect, useState } from 'react';
import { Settings, Link2, LogOut } from 'lucide-react';
import { SettingsModal } from './settings-modal';
import { useConfigStore } from '@/store/config-store';
import { wsClient } from '@/lib/websocket';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export function Layout({ children, onLogout }: { children: React.ReactNode; onLogout: () => void }) {
  const [showSettings, setShowSettings] = useState(false);
  const { apiUrl } = useConfigStore();
  const [wsStatus, setWsStatus] = useState<'connected' | 'disconnected'>('disconnected');

  useEffect(() => {
    const onConnected = wsClient.on('connected', () => setWsStatus('connected'));
    const onDisconnected = wsClient.on('disconnected', () => setWsStatus('disconnected'));
    if (wsClient.isConnected()) setWsStatus('connected');
    return () => {
      onConnected();
      onDisconnected();
    };
  }, []);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur-md supports-[backdrop-filter]:bg-background/80 shadow-sm">
        <div className="container flex h-16 items-center justify-between px-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <Link2 className="h-5 w-5 text-primary" />
            </div>
            <span className="text-xl font-bold tracking-tight">Integration Hub</span>
          </div>
          <div className="flex items-center gap-4">
            <Badge variant={wsStatus === 'connected' ? 'default' : 'secondary'}>
              {wsStatus === 'connected' ? 'Live updates connected' : 'Live updates disconnected'}
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowSettings(true)}
            >
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </Button>
            <Button variant="outline" size="sm" onClick={onLogout}>
              <LogOut className="h-4 w-4 mr-2" />
              Sign out
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto max-w-7xl">{children}</main>

      {/* Settings Modal */}
      {showSettings && (
        <SettingsModal
          open={showSettings}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
}
