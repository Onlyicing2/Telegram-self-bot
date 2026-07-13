import type { BioState } from '../lib/api';

interface Props {
  state: BioState | null;
}

function Field({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs text-on-surface-variant uppercase tracking-widest opacity-60">{label}</span>
      <span className={`text-sm text-on-surface ${mono ? 'font-mono' : ''}`}>{value || '—'}</span>
    </div>
  );
}

export default function BioStatus({ state }: Props) {
  if (!state || !state.owner_id) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-on-surface-variant">
        <p className="text-sm">Bio engine not initialized.</p>
        <p className="text-xs mt-1 opacity-60">Send <code className="font-mono">.bio on</code> in Telegram to start.</p>
      </div>
    );
  }

  const updatedAgo = (() => {
    const diff = Date.now() - new Date(state.updated_at).getTime();
    const m = Math.floor(diff / 60000);
    if (m < 1) return 'just now';
    if (m < 60) return `${m}m ago`;
    return `${Math.floor(m / 60)}h ago`;
  })();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-sm font-semibold text-on-surface-variant uppercase tracking-widest">Bio Engine</h2>
        <span className={`text-xs px-3 py-1 rounded-full font-medium ${
          state.is_active
            ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
            : 'bg-surface-variant text-on-surface-variant border border-outline-variant'
        }`}>
          {state.is_active ? 'ACTIVE' : 'INACTIVE'}
        </span>
      </div>

      <div className="bg-surface-container border border-outline-variant rounded-2xl p-5 space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="Template" value={state.template} mono />
          <Field label="Mood" value={state.mood} />
          <Field label="Custom Text" value={state.custom_text} />
          <Field label="Last Updated" value={updatedAgo} />
        </div>

        {state.last_bio && (
          <div className="pt-3 border-t border-outline-variant">
            <p className="text-xs text-on-surface-variant uppercase tracking-widest opacity-60 mb-1.5">Last Rendered Bio</p>
            <div className="bg-surface rounded-xl px-4 py-3 text-sm text-on-surface font-mono border border-outline-variant/50">
              {state.last_bio}
            </div>
          </div>
        )}
      </div>

      <div className="bg-surface-container border border-outline-variant rounded-2xl p-5">
        <p className="text-xs text-on-surface-variant uppercase tracking-widest opacity-60 mb-3">Template Tokens</p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          {[
            { token: '{time}', desc: 'Current time (HH:MM, Tehran)' },
            { token: '{mood}', desc: 'Current mood value' },
            { token: '{text}', desc: 'Custom freeform text' },
          ].map(({ token, desc }) => (
            <div key={token} className="flex flex-col gap-1 p-3 bg-surface rounded-xl border border-outline-variant/50">
              <span className="font-mono text-sm text-primary">{token}</span>
              <span className="text-xs text-on-surface-variant">{desc}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
