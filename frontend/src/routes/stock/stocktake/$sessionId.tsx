import { useState, useCallback } from 'react';
import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { AuthGuard } from '@/components/AuthGuard';
import { useUnifiedAuth } from '@/hooks/useUnifiedAuth';
import {
  useStocktakeSession,
  useStocktakeScans,
  useRecordScan,
  useCompleteSession,
  useCancelSession,
  useDiscrepancies,
} from '@/hooks/useStocktake';
import { ScanInput } from '@/components/stock/ScanInput';
import { StocktakeProgress } from '@/components/stock/StocktakeProgress';
import { DiscrepancyTable } from '@/components/stock/DiscrepancyTable';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
  ScanLine,
  ArrowLeft,
} from 'lucide-react';
import type { StocktakeScanWithProgress, SessionProgress } from '@/types/stock';

export const Route = createFileRoute('/stock/stocktake/$sessionId')({
  component: StocktakeSessionPage,
});

function StocktakeSessionPage() {
  return (
    <AuthGuard>
      <StocktakeSessionContent />
    </AuthGuard>
  );
}

function StocktakeSessionContent() {
  const { sessionId } = Route.useParams();
  const navigate = useNavigate();
  const { user } = useUnifiedAuth();
  const isAdmin = user?.role === 'admin';

  const { data: sessionDetail, isLoading } = useStocktakeSession(sessionId);
  const { data: recentScans } = useStocktakeScans(sessionId);

  const session = sessionDetail?.session;
  const isInProgress = session?.status === 'in_progress';
  const isCompleted = session?.status === 'completed';

  // Local state for scan feedback
  const [lastScanResult, setLastScanResult] = useState<StocktakeScanWithProgress | null>(null);
  const [localProgress, setLocalProgress] = useState<SessionProgress | null>(null);

  // Show discrepancies for completed sessions
  const { data: discrepancyReport } = useDiscrepancies(sessionId, isCompleted === true);

  // Confirm dialog state
  const [showCompleteConfirm, setShowCompleteConfirm] = useState(false);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);
  const [autoAdjust, setAutoAdjust] = useState(false);

  const completeSessionMutation = useCompleteSession();
  const cancelSessionMutation = useCancelSession();

  const scanMutation = useRecordScan({
    onSuccess: (data) => {
      setLastScanResult(data);
      setLocalProgress(data.session_progress);
    },
    onError: () => {
      setLastScanResult(null);
    },
  });

  const handleScan = useCallback(
    (barcodeId: string) => {
      scanMutation.mutate({
        sessionId,
        barcodeScanned: barcodeId,
      });
    },
    [sessionId, scanMutation],
  );

  const handleComplete = async () => {
    await completeSessionMutation.mutateAsync({
      sessionId,
      autoAdjust,
    });
    setShowCompleteConfirm(false);
  };

  const handleCancel = async () => {
    await cancelSessionMutation.mutateAsync(sessionId);
    setShowCancelConfirm(false);
    navigate({ to: '/stock/stocktake' });
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!session) {
    return (
      <div className="container max-w-2xl mx-auto py-6 px-4">
        <p className="text-muted-foreground">Session not found.</p>
      </div>
    );
  }

  // Use local progress if we have it (more responsive), otherwise server progress
  const progress = localProgress || sessionDetail?.progress || {
    total_expected: session.total_expected || 0,
    total_scanned: session.total_scanned || 0,
    percentage: 0,
  };

  return (
    <div className="container max-w-2xl mx-auto py-6 px-4 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate({ to: '/stock/stocktake' })}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-xl font-bold">{session.name || 'Stocktake Session'}</h1>
            <p className="text-sm text-muted-foreground">
              Started {new Date(session.started_at).toLocaleString()}
            </p>
          </div>
        </div>
        {isAdmin && isInProgress && (
          <div className="flex gap-2">
            <Button
              variant="default"
              size="sm"
              onClick={() => setShowCompleteConfirm(true)}
            >
              Complete
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowCancelConfirm(true)}
            >
              Cancel
            </Button>
          </div>
        )}
      </div>

      {/* Status Badge */}
      {!isInProgress && (
        <div
          className={`rounded-lg px-4 py-3 text-sm font-medium ${
            isCompleted
              ? 'bg-green-50 text-green-700 dark:bg-green-950/20 dark:text-green-400'
              : 'bg-gray-50 text-gray-700 dark:bg-gray-950/20 dark:text-gray-400'
          }`}
        >
          Session {session.status} on{' '}
          {session.completed_at
            ? new Date(session.completed_at).toLocaleString()
            : '—'}
        </div>
      )}

      {/* Progress */}
      <StocktakeProgress progress={progress} />

      {/* Scanner (only for in-progress sessions) */}
      {isInProgress && (
        <ScanInput
          onScan={handleScan}
          isProcessing={scanMutation.isPending}
          placeholder="Scan barcode for stocktake..."
        />
      )}

      {/* Last Scan Result */}
      {lastScanResult && isInProgress && (
        <ScanResultCard result={lastScanResult} />
      )}

      {/* Complete Confirmation */}
      {showCompleteConfirm && (
        <Card className="border-blue-300 dark:border-blue-800">
          <CardContent className="pt-6 pb-4 space-y-4">
            <p className="font-semibold">Complete this stocktake session?</p>
            <p className="text-sm text-muted-foreground">
              {progress.total_scanned} of {progress.total_expected} items scanned.
              {progress.total_expected - progress.total_scanned > 0 && (
                <span className="text-red-600 font-medium">
                  {' '}
                  {progress.total_expected - progress.total_scanned} items not yet scanned.
                </span>
              )}
            </p>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={autoAdjust}
                onChange={(e) => setAutoAdjust(e.target.checked)}
                className="rounded"
              />
              Auto-adjust stock (mark missing items as scrapped)
            </label>
            <div className="flex gap-2">
              <Button
                onClick={handleComplete}
                disabled={completeSessionMutation.isPending}
              >
                {completeSessionMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Completing...
                  </>
                ) : (
                  'Confirm Complete'
                )}
              </Button>
              <Button variant="outline" onClick={() => setShowCompleteConfirm(false)}>
                Go Back
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Cancel Confirmation */}
      {showCancelConfirm && (
        <Card className="border-red-300 dark:border-red-800">
          <CardContent className="pt-6 pb-4 space-y-4">
            <p className="font-semibold text-red-700 dark:text-red-400">
              Cancel this stocktake session?
            </p>
            <p className="text-sm text-muted-foreground">
              This will discard all scan data for this session. Stock will not be adjusted.
            </p>
            <div className="flex gap-2">
              <Button
                variant="destructive"
                onClick={handleCancel}
                disabled={cancelSessionMutation.isPending}
              >
                {cancelSessionMutation.isPending ? 'Cancelling...' : 'Yes, Cancel'}
              </Button>
              <Button variant="outline" onClick={() => setShowCancelConfirm(false)}>
                Go Back
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Discrepancy Report (after completion) */}
      {isCompleted && discrepancyReport && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold">Discrepancy Report</h2>
          <DiscrepancyTable report={discrepancyReport} />
        </div>
      )}

      {/* Recent Scans */}
      {recentScans && recentScans.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <ScanLine className="h-5 w-5" />
              Recent Scans
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-2">
            <div className="space-y-1">
              {recentScans.map((scan) => (
                <div
                  key={scan.id}
                  className="flex items-center gap-2 py-2 px-2 rounded text-sm border-b last:border-b-0"
                >
                  <ScanResultIcon result={scan.scan_result} />
                  <span className="text-muted-foreground text-xs min-w-[3rem]">
                    {new Date(scan.scanned_at).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                  <span className="font-mono text-xs truncate flex-1">
                    {scan.barcode_scanned}
                  </span>
                  <ScanResultLabel result={scan.scan_result} />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ── Helper Components ───────────────────────────────────────────────

function ScanResultCard({ result }: { result: StocktakeScanWithProgress }) {
  const { scan_result, stock_item } = result;
  const isSuccess = scan_result === 'found';

  return (
    <Card
      className={`transition-colors duration-300 ${
        isSuccess
          ? 'border-green-500 bg-green-50 dark:bg-green-950/20'
          : scan_result === 'already_scanned'
            ? 'border-amber-500 bg-amber-50 dark:bg-amber-950/20'
            : 'border-red-500 bg-red-50 dark:bg-red-950/20'
      }`}
    >
      <CardContent className="pt-6 pb-4">
        <div className="flex items-start gap-3">
          <ScanResultIcon result={scan_result} size="lg" />
          <div className="min-w-0 flex-1">
            <p
              className={`text-lg font-semibold ${
                isSuccess
                  ? 'text-green-700 dark:text-green-400'
                  : scan_result === 'already_scanned'
                    ? 'text-amber-700 dark:text-amber-400'
                    : 'text-red-700 dark:text-red-400'
              }`}
            >
              {scan_result === 'found' && 'FOUND'}
              {scan_result === 'already_scanned' && 'ALREADY SCANNED'}
              {scan_result === 'not_in_system' && 'NOT IN SYSTEM'}
              {scan_result === 'wrong_status' && 'WRONG STATUS'}
            </p>
            {stock_item && (
              <>
                <p className="text-base mt-1">
                  <span className="font-semibold">{stock_item.product_code}</span>
                  <span className="text-muted-foreground"> — {stock_item.colour}</span>
                </p>
                <p className="text-sm text-muted-foreground">
                  {stock_item.quantity} units — {stock_item.box_type === 'full' ? 'Full' : 'Partial'} box
                </p>
              </>
            )}
            <p className="text-sm font-mono text-muted-foreground mt-1">
              {result.scan.barcode_scanned}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ScanResultIcon({
  result,
  size = 'sm',
}: {
  result: string;
  size?: 'sm' | 'lg';
}) {
  const className = size === 'lg' ? 'h-8 w-8 shrink-0 mt-0.5' : 'h-4 w-4 shrink-0';

  switch (result) {
    case 'found':
      return <CheckCircle2 className={`${className} text-green-600`} />;
    case 'already_scanned':
      return <AlertTriangle className={`${className} text-amber-600`} />;
    default:
      return <XCircle className={`${className} text-red-600`} />;
  }
}

function ScanResultLabel({ result }: { result: string }) {
  const labels: Record<string, { text: string; color: string }> = {
    found: { text: 'Found', color: 'text-green-600' },
    already_scanned: { text: 'Duplicate', color: 'text-amber-600' },
    not_in_system: { text: 'Unknown', color: 'text-red-600' },
    wrong_status: { text: 'Wrong status', color: 'text-red-600' },
  };

  const label = labels[result] || { text: result, color: 'text-muted-foreground' };

  return <span className={`text-xs font-medium ${label.color}`}>{label.text}</span>;
}
