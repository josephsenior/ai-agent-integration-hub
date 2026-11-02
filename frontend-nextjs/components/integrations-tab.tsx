'use client';

import { CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import type { Integration } from '@/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Info } from 'lucide-react';

const integrations: Integration[] = [
  { name: 'Slack', type: 'slack', status: 'available', configured: false },
  { name: 'Discord', type: 'discord', status: 'available', configured: false },
  { name: 'Email', type: 'email', status: 'available', configured: false },
  { name: 'Webhook', type: 'webhook', status: 'available', configured: false },
  { name: 'WebSocket', type: 'websocket', status: 'connected', configured: true },
];

export function IntegrationsTab() {
  const getStatusIcon = (status: Integration['status']) => {
    switch (status) {
      case 'connected':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'disconnected':
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: Integration['status']) => {
    switch (status) {
      case 'connected':
        return 'bg-green-100 text-green-800';
      case 'disconnected':
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  return (
    <div className="space-y-6">
      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          Configure integrations in your backend <code className="bg-muted px-1 rounded text-xs">.env</code> file.
          WebSocket integration is automatically available when the backend is running.
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {integrations.map((integration) => (
          <Card key={integration.type} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-lg">{integration.name}</CardTitle>
                  <CardDescription className="mt-1">Type: {integration.type}</CardDescription>
                </div>
                {getStatusIcon(integration.status)}
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Status:</span>
                  <Badge
                    variant={
                      integration.status === 'connected'
                        ? 'default'
                        : integration.status === 'error'
                        ? 'destructive'
                        : 'secondary'
                    }
                  >
                    {integration.status.charAt(0).toUpperCase() + integration.status.slice(1)}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Configured:</span>
                  <Badge variant={integration.configured ? 'default' : 'outline'}>
                    {integration.configured ? 'Yes' : 'No'}
                  </Badge>
                </div>
                {!integration.configured && (
                  <div className="pt-3 border-t">
                    <p className="text-xs text-muted-foreground">
                      Add credentials to <code className="bg-muted px-1 rounded">.env</code> to enable
                      this integration.
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
