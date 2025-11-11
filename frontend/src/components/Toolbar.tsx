import type { ToneStyle } from '../config';
import { MISIX_TONE_STYLES } from '../config';

interface ToolbarProps {
  greeting: string;
  tone: ToneStyle;
  onToneChange: (tone: ToneStyle) => void;
  actions?: React.ReactNode;
}

const Toolbar = ({ greeting, tone, onToneChange, actions }: ToolbarProps) => {
  return (
    <div className="flex flex-col gap-4 rounded-lg border border-border bg-surface p-4 shadow-card">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm font-medium text-textMuted">Приветствие</p>
          <h1 className="text-xl font-semibold text-text">{greeting}</h1>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {MISIX_TONE_STYLES.map((toneOption) => (
            <button
              key={toneOption.key}
              type="button"
              onClick={() => onToneChange(toneOption.key)}
              className={`rounded-full border px-4 py-2 text-sm font-medium transition-colors ${
                tone === toneOption.key
                  ? 'border-primary bg-primaryMuted text-primary'
                  : 'border-border bg-surfaceAlt text-text'
              }`}
            >
              {toneOption.label}
            </button>
          ))}
        </div>
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
};

export default Toolbar;
