import { useState, useCallback } from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { AuthGuard } from '@/components/AuthGuard';
import { ScanInput } from '@/components/stock/ScanInput';
import { ScanResult } from '@/components/stock/ScanResult';
import { useScanIn, useScanOut, usePartialRepack, useDownloadLabel } from '@/hooks/useStock';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScanLine, CheckCircle2, XCircle, Package, Printer, PackageMinus } from 'lucide-react';
import type { ScanResponse, ScanSessionEntry, ScanMode, PartialRepackResponse } from '@/types/stock';

export const Route = createFileRoute('/stock/scan')({
  component: ScanPage,
});

function ScanPage() {
  return (
    <AuthGuard>
      <ScanContent />
    </AuthGuard>
  );
}

function ScanContent() {
  const [scanMode, setScanMode] = useState<ScanMode>('stock_in');
  const [lastResult, setLastResult] = useState<ScanResponse | null>(null);
  const [sessionScans, setSessionScans] = useState<ScanSessionEntry[]>([]);

  // Partial box state
  const [showPartialPrompt, setShowPartialPrompt] = useState(false);
  const [partialBarcodeId, setPartialBarcodeId] = useState<string | null>(null);
  const [partialQuantity, setPartialQuantity] = useState<string>('');
  const [partialBoxQuantity, setPartialBoxQuantity] = useState<number>(0);
  const [partialResult, setPartialResult] = useState<PartialRepackResponse | null>(null);

  const addSessionScan = useCallback(
    (entry: ScanSessionEntry) => {
      setSessionScans((prev) => [entry, ...prev.slice(0, 19)]);
    },
    [],
  );

  // ── Scan In ──────────────────────────────────────────────────────

  const scanInMutation = useScanIn({
    onSuccess: (data) => {
      setLastResult(data);
      addSessionScan({
        barcode_id: data.barcode_id || '',
        success: data.success,
        message: data.message,
        product_code: data.stock_item?.product_code,
        colour: data.stock_item?.colour,
        quantity: data.stock_item?.quantity,
        timestamp: new Date(),
      });
    },
    onError: (error) => {
      const errorResult: ScanResponse = {
        success: false,
        stock_item: null,
        movement: null,
        message: error.message,
        error: error.message,
        barcode_id: null,
        product_description: null,
      };
      setLastResult(errorResult);
    },
  });

  // ── Scan Out ─────────────────────────────────────────────────────

  const scanOutMutation = useScanOut({
    onSuccess: (data) => {
      setLastResult(data);
      addSessionScan({
        barcode_id: data.barcode_id || '',
        success: data.success,
        message: data.message,
        product_code: data.stock_item?.product_code,
        colour: data.stock_item?.colour,
        quantity: data.stock_item?.quantity,
        timestamp: new Date(),
      });
      // Show partial box prompt on successful scan-out
      if (data.success && data.stock_item) {
        setShowPartialPrompt(true);
        setPartialBarcodeId(data.barcode_id);
        setPartialBoxQuantity(data.stock_item.quantity);
        setPartialResult(null);
        setPartialQuantity('');
      }
    },
    onError: (error) => {
      const errorResult: ScanResponse = {
        success: false,
        stock_item: null,
        movement: null,
        message: error.message,
        error: error.message,
        barcode_id: null,
        product_description: null,
      };
      setLastResult(errorResult);
      setShowPartialPrompt(false);
    },
  });

  // ── Partial Repack ───────────────────────────────────────────────

  const partialRepackMutation = usePartialRepack({
    onSuccess: (data) => {
      setPartialResult(data);
      if (data.success) {
        setShowPartialPrompt(false);
      }
    },
    onError: (error) => {
      setPartialResult({
        success: false,
        original_item: null,
        new_partial_item: null,
        units_taken: 0,
        units_remaining: 0,
        label_url: null,
        message: error.message,
        error: error.message,
      });
    },
  });

  const downloadLabelMutation = useDownloadLabel();

  // ── Handlers ─────────────────────────────────────────────────────

  const handleScan = useCallback(
    (barcodeId: string) => {
      // Reset partial state on new scan
      setShowPartialPrompt(false);
      setPartialResult(null);

      if (scanMode === 'stock_in') {
        scanInMutation.mutate(barcodeId);
      } else {
        scanOutMutation.mutate({ barcodeId });
      }
    },
    [scanMode, scanInMutation, scanOutMutation],
  );

  const handleModeChange = useCallback((mode: ScanMode) => {
    setScanMode(mode);
    setLastResult(null);
    setShowPartialPrompt(false);
    setPartialResult(null);
  }, []);

  const handlePartialConfirm = useCallback(() => {
    const unitsTaken = parseInt(partialQuantity, 10);
    if (!partialBarcodeId || isNaN(unitsTaken) || unitsTaken <= 0) return;

    partialRepackMutation.mutate({
      barcodeId: partialBarcodeId,
      unitsTaken,
    });
  }, [partialBarcodeId, partialQuantity, partialRepackMutation]);

  const handlePrintLabel = useCallback(() => {
    if (partialResult?.new_partial_item?.barcode_id) {
      downloadLabelMutation.mutate(partialResult.new_partial_item.barcode_id);
    }
  }, [partialResult, downloadLabelMutation]);

  const remaining = partialQuantity
    ? partialBoxQuantity - parseInt(partialQuantity, 10)
    : partialBoxQuantity;
  const unitsTakenNum = parseInt(partialQuantity, 10);
  const isPartialValid =
    !isNaN(unitsTakenNum) && unitsTakenNum > 0 && unitsTakenNum < partialBoxQuantity;

  // Session summary
  const successScans = sessionScans.filter((s) => s.success);
  const totalCartons = successScans.length;
  const totalUnits = successScans.reduce((sum, s) => sum + (s.quantity || 0), 0);

  const isProcessing = scanInMutation.isPending || scanOutMutation.isPending;

  return (
    <div className="container max-w-2xl mx-auto py-6 px-4 space-y-6">
      {/* Mode Toggle */}
      <div className="flex gap-3">
        <button
          type="button"
          onClick={() => handleModeChange('stock_in')}
          className={`flex-1 h-14 rounded-lg text-lg font-semibold transition-colors ${
            scanMode === 'stock_in'
              ? 'bg-green-600 text-white shadow-md'
              : 'bg-muted text-muted-foreground hover:bg-muted/80'
          }`}
        >
          STOCK IN
        </button>
        <button
          type="button"
          onClick={() => handleModeChange('stock_out')}
          className={`flex-1 h-14 rounded-lg text-lg font-semibold transition-colors ${
            scanMode === 'stock_out'
              ? 'bg-blue-600 text-white shadow-md'
              : 'bg-muted text-muted-foreground hover:bg-muted/80'
          }`}
        >
          STOCK OUT
        </button>
      </div>

      {/* Scanner Input */}
      <ScanInput
        onScan={handleScan}
        isProcessing={isProcessing}
        placeholder={
          scanMode === 'stock_in'
            ? 'Scan barcode to stock in...'
            : 'Scan barcode to stock out...'
        }
      />

      {/* Last Scan Result */}
      {lastResult && (
        <div>
          <p className="text-sm font-medium text-muted-foreground mb-2">
            Last Scan Result:
          </p>
          <ScanResult result={lastResult} mode={scanMode} />
        </div>
      )}

      {/* Partial Box Prompt (after successful scan-out) */}
      {showPartialPrompt && scanMode === 'stock_out' && (
        <Card className="border-amber-400 bg-amber-50 dark:bg-amber-950/20">
          <CardContent className="pt-6 pb-4">
            <div className="flex items-start gap-3">
              <PackageMinus className="h-6 w-6 text-amber-600 shrink-0 mt-1" />
              <div className="flex-1 space-y-3">
                <p className="text-base font-semibold text-amber-700 dark:text-amber-400">
                  Partial box? Only took some units?
                </p>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-amber-800 dark:text-amber-300">
                    Units taken from this box:
                  </label>
                  <Input
                    type="number"
                    min={1}
                    max={partialBoxQuantity - 1}
                    value={partialQuantity}
                    onChange={(e) => setPartialQuantity(e.target.value)}
                    placeholder={`1 to ${partialBoxQuantity - 1}`}
                    className="h-12 text-lg bg-white dark:bg-background"
                  />
                  {partialQuantity && isPartialValid && (
                    <p className="text-sm text-amber-700 dark:text-amber-400">
                      Remaining: <span className="font-semibold">{remaining}</span> units
                    </p>
                  )}
                  {partialQuantity && !isPartialValid && unitsTakenNum > 0 && (
                    <p className="text-sm text-red-600">
                      Must be less than {partialBoxQuantity} (full box quantity)
                    </p>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button
                    onClick={handlePartialConfirm}
                    disabled={!isPartialValid || partialRepackMutation.isPending}
                    className="bg-amber-600 hover:bg-amber-700 text-white"
                  >
                    {partialRepackMutation.isPending ? 'Processing...' : 'Confirm Partial'}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setShowPartialPrompt(false)}
                  >
                    Skip — took whole box
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Partial Repack Result */}
      {partialResult && partialResult.success && (
        <Card className="border-yellow-400 bg-yellow-50 dark:bg-yellow-950/20">
          <CardContent className="pt-6 pb-4">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="h-8 w-8 text-yellow-600 shrink-0 mt-0.5" />
              <div className="flex-1 space-y-2">
                <p className="text-lg font-semibold text-yellow-700 dark:text-yellow-400">
                  PARTIAL REPACK COMPLETE
                </p>
                <p className="text-base">
                  New label:{' '}
                  <span className="font-mono font-semibold">
                    {partialResult.new_partial_item?.barcode_id}
                  </span>
                </p>
                <p className="text-base text-muted-foreground">
                  {partialResult.units_remaining} units remaining — PARTIAL BOX
                </p>
                <Button
                  onClick={handlePrintLabel}
                  disabled={downloadLabelMutation.isPending}
                  className="bg-yellow-600 hover:bg-yellow-700 text-white mt-2"
                >
                  <Printer className="h-4 w-4 mr-2" />
                  {downloadLabelMutation.isPending
                    ? 'Downloading...'
                    : 'Print Yellow Label'}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {partialResult && !partialResult.success && (
        <Card className="border-red-500 bg-red-50 dark:bg-red-950/20">
          <CardContent className="pt-6 pb-4">
            <div className="flex items-start gap-3">
              <XCircle className="h-8 w-8 text-red-600 shrink-0 mt-0.5" />
              <div>
                <p className="text-lg font-semibold text-red-700 dark:text-red-400">
                  PARTIAL REPACK FAILED
                </p>
                <p className="text-base mt-1">
                  {partialResult.error || partialResult.message}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Session Summary */}
      {sessionScans.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Package className="h-5 w-5" />
              Session Summary
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <div className="flex gap-8 text-base">
              <div>
                <span className="text-muted-foreground">Cartons: </span>
                <span className="font-semibold">{totalCartons}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Units: </span>
                <span className="font-semibold">{totalUnits.toLocaleString()}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Scans */}
      {sessionScans.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <ScanLine className="h-5 w-5" />
              Recent Scans
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-2">
            <div className="space-y-1">
              {sessionScans.map((scan, idx) => (
                <div
                  key={`${scan.barcode_id}-${idx}`}
                  className="flex items-center gap-2 py-2 px-2 rounded text-sm border-b last:border-b-0"
                >
                  {scan.success ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0" />
                  ) : (
                    <XCircle className="h-4 w-4 text-red-600 shrink-0" />
                  )}
                  <span className="text-muted-foreground text-xs min-w-[3rem]">
                    {scan.timestamp.toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                  <span className="font-mono text-xs truncate flex-1">
                    {scan.barcode_id || '—'}
                  </span>
                  <span
                    className={`text-xs font-medium ${
                      scan.success ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    {scan.success
                      ? scanMode === 'stock_in'
                        ? 'In'
                        : 'Out'
                      : 'Error'}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
