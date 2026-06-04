"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { fetchProgress } from "@/lib/api";
import { ProgressData } from "@/lib/types";

export default function ProgressPage() {
  const [data,    setData]    = useState<ProgressData | null>(null);
  const [loading, setLoading] = useState(true);
  const { getToken, userId } = useAuth();

  useEffect(() => {
    (async () => {
      if (!userId) return;
      try {
        const token = await getToken();
        const uid   = `web_${userId}`;
        const d = await fetchProgress(uid, token);
        setData(d);
      } catch (_) {}
      finally { setLoading(false); }
    })();
  }, [userId, getToken]);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/study" className="text-slate-400 hover:text-slate-700 text-sm">← Volver al tutor</Link>
            <span className="text-slate-300">|</span>
            <span className="font-semibold text-sm text-slate-800">📊 Mi Progreso</span>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-10">
        {loading ? (
          <div className="text-center py-20 text-slate-400">Cargando...</div>
        ) : !data || data.total_answered === 0 ? (
          <div className="text-center py-20">
            <div className="text-4xl mb-4">📊</div>
            <h2 className="text-xl font-semibold text-slate-700 mb-2">Sin datos todavía</h2>
            <p className="text-slate-400 text-sm mb-6">Responde algunas preguntas para ver tu progreso.</p>
            <Link href="/study" className="bg-blue-600 text-white px-6 py-2.5 rounded-xl text-sm font-semibold hover:bg-blue-700 transition-colors">
              Ir a estudiar →
            </Link>
          </div>
        ) : (
          <ProgressDashboard data={data} />
        )}
      </div>
    </div>
  );
}

function ProgressDashboard({ data }: { data: ProgressData }) {
  const pct = data.overall_accuracy;
  const accentColor = pct >= 70 ? "text-green-600" : pct >= 50 ? "text-amber-600" : "text-red-500";
  const barColor    = pct >= 70 ? "bg-green-500"   : pct >= 50 ? "bg-amber-400"   : "bg-red-400";

  return (
    <div className="space-y-8">
      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-4">
        <StatCard label="Preguntas respondidas" value={String(data.total_answered)} />
        <StatCard label="Respuestas correctas"  value={String(data.total_correct)} />
        <StatCard
          label="Precisión general"
          value={`${pct}%`}
          valueClass={accentColor}
        />
      </div>

      {/* Overall bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6">
        <h2 className="font-semibold text-slate-800 mb-4">Rendimiento global</h2>
        <div className="flex items-center gap-4">
          <div className="flex-1 h-4 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${barColor}`}
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className={`text-2xl font-bold ${accentColor}`}>{pct}%</span>
        </div>
        <p className="text-xs text-slate-400 mt-2">
          {pct >= 70 ? "¡Excelente! Sigue así." : pct >= 50 ? "Buen progreso. Foco en los temas débiles." : "Todavía queda trabajo. Revisa la fisiopatología base."}
        </p>
      </div>

      {/* By topic */}
      {data.by_topic.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6">
          <h2 className="font-semibold text-slate-800 mb-5">Por tema</h2>
          <div className="space-y-4">
            {data.by_topic
              .sort((a, b) => a.accuracy - b.accuracy)  // weakest first
              .map((t) => (
                <TopicRow key={t.topic} label={t.topic} total={t.total} correct={t.correct} accuracy={t.accuracy} />
              ))}
          </div>
        </div>
      )}

      {/* By step */}
      {data.by_step.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6">
          <h2 className="font-semibold text-slate-800 mb-5">Por Step</h2>
          <div className="space-y-4">
            {data.by_step.map((s) => (
              <TopicRow key={s.step} label={`USMLE Step ${s.step}`} total={s.total} correct={s.correct} accuracy={s.accuracy} />
            ))}
          </div>
        </div>
      )}

      <div className="text-center">
        <Link href="/study" className="bg-blue-600 text-white px-8 py-3 rounded-xl text-sm font-semibold hover:bg-blue-700 transition-colors">
          Continuar estudiando →
        </Link>
      </div>
    </div>
  );
}

function StatCard({ label, value, valueClass = "text-slate-900" }: { label: string; value: string; valueClass?: string }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 text-center">
      <p className={`text-3xl font-bold mb-1 ${valueClass}`}>{value}</p>
      <p className="text-xs text-slate-400">{label}</p>
    </div>
  );
}

function TopicRow({ label, total, correct, accuracy }: { label: string; total: number; correct: number; accuracy: number }) {
  const color = accuracy >= 70 ? "bg-green-500" : accuracy >= 50 ? "bg-amber-400" : "bg-red-400";
  const textColor = accuracy >= 70 ? "text-green-700" : accuracy >= 50 ? "text-amber-700" : "text-red-600";
  return (
    <div className="flex items-center gap-4">
      <span className="text-sm text-slate-600 w-36 capitalize truncate">{label}</span>
      <div className="flex-1 h-2.5 bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${accuracy}%` }} />
      </div>
      <span className={`text-sm font-semibold w-12 text-right ${textColor}`}>{accuracy}%</span>
      <span className="text-xs text-slate-400 w-16 text-right">{correct}/{total}</span>
    </div>
  );
}
