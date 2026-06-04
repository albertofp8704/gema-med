"use client";

import { ProgressData } from "@/lib/types";

interface Props {
  data: ProgressData | null;
}

export default function ProgressPanel({ data }: Props) {
  if (!data || data.total_answered === 0) {
    return (
      <p className="text-xs text-slate-500 px-1">Sin datos aún. Responde tu primera pregunta.</p>
    );
  }

  const pct = data.overall_accuracy;
  const color = pct >= 70 ? "#22C55E" : pct >= 50 ? "#F59E0B" : "#EF4444";

  return (
    <div className="space-y-2">
      {/* Overall */}
      <div className="bg-brand-900/40 rounded-xl p-3 space-y-2">
        <div className="flex justify-between text-xs text-slate-400">
          <span>Preguntas</span>
          <span className="text-white font-semibold">
            {data.total_correct}/{data.total_answered}
          </span>
        </div>
        <div className="flex justify-between text-xs text-slate-400">
          <span>Precisión</span>
          <span className="font-bold" style={{ color }}>{pct}%</span>
        </div>
        {/* Bar */}
        <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${pct}%`,
              background: `linear-gradient(90deg, #2563EB, #60A5FA)`,
            }}
          />
        </div>
      </div>

      {/* By topic (top 5) */}
      <div className="space-y-1">
        {data.by_topic.slice(0, 5).map((t) => (
          <div key={t.topic} className="flex items-center justify-between text-xs">
            <span className="text-slate-400 truncate max-w-[110px]">{t.topic}</span>
            <span
              className="font-semibold ml-2"
              style={{ color: t.accuracy >= 70 ? "#4ADE80" : t.accuracy >= 50 ? "#FCD34D" : "#F87171" }}
            >
              {t.accuracy}%
            </span>
          </div>
        ))}
      </div>

      {/* By step */}
      {data.by_step.length > 0 && (
        <div className="border-t border-slate-700 pt-2 space-y-1">
          {data.by_step.map((s) => (
            <div key={s.step} className="flex justify-between text-xs">
              <span className="text-slate-400">Step {s.step}</span>
              <span className="text-slate-300">{s.correct}/{s.total}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
