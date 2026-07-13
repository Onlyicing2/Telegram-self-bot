import { useState } from 'react';
import type { BotLog } from '../lib/api';

interface Props {
  logs: BotLog[];
}

const LEVEL_STYLES: Record<string, string> = {
  INFO:  'text-sky-400 bg-sky-400/10',
  WARN:  'text-amber-400 bg-amber-400/10',
  ERROR: 'text-red-400 bg-red-400/10',
};

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString('en-US', { hour12: false });
}

export default function LogViewer({ logs }: Props) {
  const [filter, setFilter] = useState<'ALL' | 'INFO' | 'WARN' | 'ERROR'>('ALL');

  const filtered = filter === 'ALL' ? logs : logs.filter(l => l.level === filter);

  if (!logs.length) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-on-surface-variant">
        <p className="text-sm">No logs recorded yet.</p>
      </div>
    );
  }

  const counts = {
    ALL: logs.length,
    INFO: logs.filter(l => l.level === 'INFO').length,
    WARN: logs.filter(l => l.level === 'WARN').length,
    ERROR: logs.filter(l => l.level === 'ERROR').length,
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-on-surface-variant uppercase tracking-widest">Logs</h2>
        <div className="flex gap-1">
          {(['ALL', 'INFO', 'WARN', 'ERROR'] as const).map(lvl => (
            <button
              key={lvl}
              onClick={() => setFilter(lvl)}
              className={`text-xs px-2.5 py-1 rounded-full transition-colors ${
                filter === lvl
                  ? 'bg-primary text-on-primary'
                  : 'text-on-surface-variant hover:bg-surface-variant'
              }`}
            >
              {lvl} {counts[lvl] > 0 && <span className="opacity-70">{counts[lvl]}</span>}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-surface-container border border-outline-variant rounded-2xl overflow-hidden">
        <div className="divide-y divide-outline-variant/50 max-h-[600px] overflow-y-auto">
          {filtered.length === 0 ? (
            <div className="px-5 py-8 text-center text-sm text-on-surface-variant">
              No {filter} logs.
            </div>
          ) : (
            filtered.map(log => (
              <div key={log.id} className="px-5 py-3 flex items-start gap-3 hover:bg-surface-variant/30 transition-colors">
                <span className={`shrink-0 text-xs font-mono px-2 py-0.5 rounded-full mt-0.5 ${LEVEL_STYLES[log.level] || ''}`}>
                  {log.level}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-on-surface leading-snug">{log.message}</p>
                  {log.context && Object.keys(log.context).length > 0 && (
                    <p className="text-xs text-on-surface-variant mt-0.5 font-mono truncate">
                      {JSON.stringify(log.context)}
                    </p>
                  )}
                </div>
                <span className="shrink-0 text-xs text-on-surface-variant font-mono">
                  {formatTime(log.created_at)}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
