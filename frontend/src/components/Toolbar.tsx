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
    <div className="flex flex-col gap-5 rounded-2xl border border-borderStrong bg-surface/70 p-6 shadow-card backdrop-blur-xl">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-textMuted">Приветствие</p>
          <h1 className="text-2xl font-semibold text-text md:text-3xl">{greeting}</h1>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {MISIX_TONE_STYLES.map((toneOption) => (
            <button
              key={toneOption.key}
              type="button"
              onClick={() => onToneChange(toneOption.key)}
              className={`group relative overflow-hidden rounded-full border px-4 py-2 text-sm font-medium transition-all duration-350 ease-out-soft ${
                tone === toneOption.key
                  ? 'border-primary bg-primaryMuted text-primary shadow-glow'
                  : 'border-borderStrong bg-surfaceGlass text-textSecondary hover:text-text'
              }`}
            >
              <span className="pointer-events-none absolute inset-0 translate-x-[-120%] bg-[linear-gradient(120deg,transparent,rgba(255,255,255,0.35),transparent)] transition-transform duration-500 group-hover:translate-x-[120%]" aria-hidden="true" />
              {toneOption.label}
            </button>
          ))}
        </div>
      </div>
      {actions && <div className="flex flex-wrap gap-3">{actions}</div>}
    </div>
  );
};

export default Toolbar;
