import { useEffect, useRef } from 'react';
import { CheckCircle2, XCircle } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import type { ScanResponse, ScanMode } from '@/types/stock';

interface ScanResultProps {
  result: ScanResponse | null;
  mode?: ScanMode;
}

// ── Audio Feedback ──────────────────────────────────────────────────

let audioCtx: AudioContext | null = null;

function getAudioContext(): AudioContext {
  if (!audioCtx) {
    audioCtx = new AudioContext();
  }
  return audioCtx;
}

function playSuccessBeep() {
  try {
    const ctx = getAudioContext();
    const oscillator = ctx.createOscillator();
    const gain = ctx.createGain();

    oscillator.connect(gain);
    gain.connect(ctx.destination);

    oscillator.type = 'sine';
    oscillator.frequency.setValueAtTime(880, ctx.currentTime); // A5
    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.15);

    oscillator.start(ctx.currentTime);
    oscillator.stop(ctx.currentTime + 0.15);
  } catch {
    // Audio not available — ignore silently
  }
}

function playErrorTone() {
  try {
    const ctx = getAudioContext();
    const oscillator = ctx.createOscillator();
    const gain = ctx.createGain();

    oscillator.connect(gain);
    gain.connect(ctx.destination);

    oscillator.type = 'square';
    oscillator.frequency.setValueAtTime(220, ctx.currentTime); // A3 — low
    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);

    oscillator.start(ctx.currentTime);
    oscillator.stop(ctx.currentTime + 0.3);
  } catch {
    // Audio not available — ignore silently
  }
}

// ── Component ───────────────────────────────────────────────────────

export function ScanResult({ result, mode = 'stock_in' }: ScanResultProps) {
  const prevResultRef = useRef<ScanResponse | null>(null);

  // Play audio feedback when a new result arrives
  useEffect(() => {
    if (!result || result === prevResultRef.current) return;
    prevResultRef.current = result;

    if (result.success) {
      playSuccessBeep();
    } else {
      playErrorTone();
    }
  }, [result]);

  if (!result) return null;

  const item = result.stock_item;

  return (
    <Card
      className={`transition-colors duration-300 ${
        result.success
          ? 'border-green-500 bg-green-50 dark:bg-green-950/20'
          : 'border-red-500 bg-red-50 dark:bg-red-950/20'
      }`}
    >
      <CardContent className="pt-6 pb-4">
        <div className="flex items-start gap-3">
          {result.success ? (
            <CheckCircle2 className="h-8 w-8 text-green-600 shrink-0 mt-0.5" />
          ) : (
            <XCircle className="h-8 w-8 text-red-600 shrink-0 mt-0.5" />
          )}

          <div className="min-w-0 flex-1">
            <p
              className={`text-lg font-semibold ${
                result.success ? 'text-green-700 dark:text-green-400' : 'text-red-700 dark:text-red-400'
              }`}
            >
              {result.success
                ? mode === 'stock_out'
                  ? 'SCANNED OUT'
                  : 'SCANNED IN'
                : 'SCAN FAILED'}
            </p>

            {result.success && item ? (
              <>
                <p className="text-base mt-1">
                  <span className="font-semibold">{item.product_code}</span>
                  {result.product_description && (
                    <span className="text-muted-foreground">
                      {' '}
                      — {result.product_description}
                    </span>
                  )}
                </p>
                <p className="text-base text-muted-foreground">
                  {item.colour} — {item.quantity} units —{' '}
                  {item.box_type === 'full' ? 'Full box' : 'Partial box'}
                </p>
                <p className="text-sm font-mono text-muted-foreground mt-1">
                  {item.barcode_id}
                </p>
              </>
            ) : (
              <>
                <p className="text-base mt-1">{result.error || result.message}</p>
                {result.barcode_id && (
                  <p className="text-sm font-mono text-muted-foreground mt-1">
                    {result.barcode_id}
                  </p>
                )}
              </>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
