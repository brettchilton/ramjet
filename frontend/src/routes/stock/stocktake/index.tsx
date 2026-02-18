import { useState } from 'react';
import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { AuthGuard } from '@/components/AuthGuard';
import { useUnifiedAuth } from '@/hooks/useUnifiedAuth';
import { useStocktakeSessions, useStartSession } from '@/hooks/useStocktake';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ClipboardList, Plus, Loader2 } from 'lucide-react';
import type { StocktakeSession } from '@/types/stock';

export const Route = createFileRoute('/stock/stocktake/')({
  component: StocktakeListPage,
});

function StocktakeListPage() {
  return (
    <AuthGuard>
      <StocktakeListContent />
    </AuthGuard>
  );
}

function StocktakeListContent() {
  const { user } = useUnifiedAuth();
  const navigate = useNavigate();
  const { data: sessions, isLoading } = useStocktakeSessions();
  const startSessionMutation = useStartSession();

  const [showNewForm, setShowNewForm] = useState(false);
  const [newName, setNewName] = useState('');

  // Admin only
  if (user?.role !== 'admin') {
    return (
      <div className="container max-w-4xl mx-auto py-6 px-4">
        <p className="text-muted-foreground">Stocktake management is admin only.</p>
      </div>
    );
  }

  const handleStartSession = async () => {
    if (!newName.trim()) return;
    const session = await startSessionMutation.mutateAsync({
      name: newName.trim(),
    });
    setShowNewForm(false);
    setNewName('');
    navigate({ to: '/stock/stocktake/$sessionId', params: { sessionId: session.id } });
  };

  const getStatusBadge = (status: StocktakeSession['status']) => {
    switch (status) {
      case 'in_progress':
        return (
          <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
            In Progress
          </span>
        );
      case 'completed':
        return (
          <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800 dark:bg-green-900/30 dark:text-green-400">
            Completed
          </span>
        );
      case 'cancelled':
        return (
          <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800 dark:bg-gray-900/30 dark:text-gray-400">
            Cancelled
          </span>
        );
    }
  };

  return (
    <div className="container max-w-4xl mx-auto py-6 px-4 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <ClipboardList className="h-6 w-6" />
          Stocktake Sessions
        </h1>
        {!showNewForm && (
          <Button onClick={() => setShowNewForm(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Start New
          </Button>
        )}
      </div>

      {/* New Session Form */}
      {showNewForm && (
        <Card>
          <CardContent className="pt-6 pb-4">
            <div className="space-y-3">
              <label className="text-sm font-medium">Session Name</label>
              <Input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="e.g. Q1 2026 Stocktake"
                className="h-12 text-lg"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleStartSession();
                  if (e.key === 'Escape') setShowNewForm(false);
                }}
              />
              <div className="flex gap-2">
                <Button
                  onClick={handleStartSession}
                  disabled={!newName.trim() || startSessionMutation.isPending}
                >
                  {startSessionMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Starting...
                    </>
                  ) : (
                    'Start Session'
                  )}
                </Button>
                <Button variant="outline" onClick={() => setShowNewForm(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Sessions List */}
      {isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : !sessions?.length ? (
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-muted-foreground">No stocktake sessions yet.</p>
            <p className="text-sm text-muted-foreground mt-1">
              Start a new session to begin a quarterly stocktake.
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b text-left text-sm text-muted-foreground">
                    <th className="p-4">Name</th>
                    <th className="p-4">Status</th>
                    <th className="p-4">Date</th>
                    <th className="p-4 text-right">Expected</th>
                    <th className="p-4 text-right">Scanned</th>
                    <th className="p-4 text-right">Discrepancies</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.map((session) => (
                    <tr
                      key={session.id}
                      className="border-b last:border-b-0 hover:bg-muted/50 cursor-pointer transition-colors"
                      onClick={() =>
                        navigate({
                          to: '/stock/stocktake/$sessionId',
                          params: { sessionId: session.id },
                        })
                      }
                    >
                      <td className="p-4 font-medium">{session.name || '—'}</td>
                      <td className="p-4">{getStatusBadge(session.status)}</td>
                      <td className="p-4 text-sm text-muted-foreground">
                        {new Date(session.started_at).toLocaleDateString()}
                      </td>
                      <td className="p-4 text-right">{session.total_expected ?? '—'}</td>
                      <td className="p-4 text-right">{session.total_scanned ?? '—'}</td>
                      <td className="p-4 text-right">
                        {session.total_discrepancies != null ? (
                          <span
                            className={
                              session.total_discrepancies > 0
                                ? 'text-red-600 font-medium'
                                : 'text-green-600'
                            }
                          >
                            {session.total_discrepancies}
                          </span>
                        ) : (
                          '—'
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
