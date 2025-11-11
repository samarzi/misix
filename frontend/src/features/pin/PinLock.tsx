import { useCallback, useMemo, useState } from 'react';
import Button from '../../components/Button';
import { useUiStore } from '../../stores/uiStore';

interface PinLockProps {
  onUnlock: (pin: string) => Promise<void> | void;
  onReset?: () => Promise<void> | void;
}

const PIN_LENGTH = 4;
const INITIAL_ENTRY = Array(PIN_LENGTH).fill('');

const PinLock = ({ onUnlock, onReset }: PinLockProps) => {
  const { pin, setPinState } = useUiStore();
  const [entry, setEntry] = useState<string[]>(INITIAL_ENTRY);
  const [isLoading, setLoading] = useState(false);

  const isComplete = useMemo(() => entry.every((digit) => digit !== ''), [entry]);

  const handleNumpadPress = useCallback(
    async (value: string) => {
      if (isLoading) return;

      if (value === 'backspace') {
        setEntry((prev) => {
          const copy = [...prev];
          let lastIndex = -1;
          for (let i = copy.length - 1; i >= 0; i -= 1) {
            if (copy[i] !== '') {
              lastIndex = i;
              break;
            }
          }
          if (lastIndex >= 0) {
            copy[lastIndex] = '';
          }
          return copy;
        });
        setPinState({ error: null });
        return;
      }

      if (value === 'clear') {
        setEntry(INITIAL_ENTRY);
        setPinState({ error: null });
        return;
      }

      setEntry((prev) => {
        const copy = [...prev];
        const firstEmptyIndex = copy.findIndex((digit) => digit === '');
        if (firstEmptyIndex >= 0) {
          copy[firstEmptyIndex] = value;
        }
        return copy;
      });
    },
    [isLoading, setPinState],
  );

  const handleUnlock = useCallback(async () => {
    if (!isComplete || isLoading) return;
    const pinCode = entry.join('');
    try {
      setLoading(true);
      await onUnlock(pinCode);
      setPinState({ locked: false, error: null });
    } catch (error) {
      console.error('Failed to unlock dashboard', error);
      setPinState({ locked: true, error: 'Неверный PIN. Попробуй еще раз.' });
      setEntry(INITIAL_ENTRY);
    } finally {
      setLoading(false);
    }
  }, [entry, isComplete, isLoading, onUnlock, setPinState]);

  const numpadKeys = useMemo(
    () => [
      ['1', '2', '3'],
      ['4', '5', '6'],
      ['7', '8', '9'],
      ['clear', '0', 'backspace'],
    ],
    [],
  );

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-10">
      <div className="w-full max-w-sm rounded-2xl border border-border bg-surface p-6 text-center shadow-card">
        <h2 className="text-xl font-semibold text-text">Разблокируй дашборд</h2>
        <p className="mt-2 text-sm text-textMuted">Введи PIN, чтобы продолжить работу.</p>

        <div className="mt-6 flex justify-center gap-4">
          {entry.map((digit, index) => (
            <div
              key={index}
              className={`h-4 w-4 rounded-full border border-border ${digit ? 'bg-primary border-primary' : 'bg-transparent'}`}
            />
          ))}
        </div>

        {pin.error && <p className="mt-3 text-sm text-danger">{pin.error}</p>}

        <div className="mt-6 grid grid-cols-3 gap-3">
          {numpadKeys.flat().map((key) => (
            <button
              key={key}
              type="button"
              onClick={() => handleNumpadPress(key)}
              className="rounded-lg border border-border bg-surfaceAlt py-4 text-lg font-semibold text-text shadow-card hover:bg-surface"
            >
              {key === 'backspace' ? '⌫' : key === 'clear' ? 'Очистить' : key}
            </button>
          ))}
        </div>

        <Button
          className="mt-6 w-full"
          onClick={handleUnlock}
          disabled={!isComplete || isLoading}
        >
          {isLoading ? 'Проверяю...' : 'Разблокировать'}
        </Button>

        {onReset && (
          <button
            type="button"
            onClick={() => onReset()}
            className="mt-3 text-sm text-primary underline-offset-2 hover:underline"
          >
            Не помню PIN
          </button>
        )}
      </div>
    </div>
  );
};

export default PinLock;
