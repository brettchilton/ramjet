import { useRef, useEffect, useCallback, useState } from 'react';
import { Input } from '@/components/ui/input';
import { Loader2 } from 'lucide-react';

interface ScanInputProps {
  onScan: (barcodeId: string) => void;
  isProcessing: boolean;
  placeholder?: string;
  disabled?: boolean;
}

/**
 * Auto-focused scanner input for Zebra DS22 Bluetooth HID integration.
 *
 * The scanner "types" the QR content into the focused text field,
 * followed by an Enter keystroke which triggers form submission.
 * After each scan, the input auto-clears and re-focuses.
 */
export function ScanInput({
  onScan,
  isProcessing,
  placeholder = 'Scan barcode or enter manually...',
  disabled = false,
}: ScanInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [value, setValue] = useState('');
  const lastSubmitRef = useRef<number>(0);

  // Auto-focus on mount and after processing
  useEffect(() => {
    if (!isProcessing && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isProcessing]);

  // Re-focus when the user taps elsewhere on the page (tablet use case)
  useEffect(() => {
    const refocus = () => {
      // Small delay to let the tap event settle
      setTimeout(() => {
        if (inputRef.current && document.activeElement !== inputRef.current && !disabled) {
          inputRef.current.focus();
        }
      }, 100);
    };

    document.addEventListener('click', refocus);
    return () => document.removeEventListener('click', refocus);
  }, [disabled]);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();

      const trimmed = value.trim();
      if (!trimmed || isProcessing || disabled) return;

      // Debounce rapid scans (prevent double-submit within 300ms)
      const now = Date.now();
      if (now - lastSubmitRef.current < 300) return;
      lastSubmitRef.current = now;

      onScan(trimmed);
      setValue('');
    },
    [value, isProcessing, disabled, onScan],
  );

  return (
    <form onSubmit={handleSubmit} className="relative">
      <Input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={placeholder}
        disabled={isProcessing || disabled}
        className="h-14 text-lg pr-12 font-mono"
        autoComplete="off"
        autoCorrect="off"
        autoCapitalize="off"
        spellCheck={false}
        // inputMode="none" prevents virtual keyboard on tablets
        // but allows physical keyboard/scanner input
        inputMode="none"
      />
      {isProcessing && (
        <div className="absolute right-3 top-1/2 -translate-y-1/2">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      )}
    </form>
  );
}
