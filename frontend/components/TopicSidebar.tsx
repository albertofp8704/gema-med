"use client";

import Link from "next/link";
import { UserButton } from "@clerk/nextjs";
import { TOPICS } from "@/lib/types";
import ProgressPanel from "./ProgressPanel";
import { ProgressData } from "@/lib/types";

interface Props {
  activeTopic: string | null;
  activeStep: number | null;
  progress: ProgressData | null;
  onTopic: (t: string | null) => void;
  onStep: (s: number | null) => void;
  onReset: () => void;
}

export default function TopicSidebar({
  activeTopic,
  activeStep,
  progress,
  onTopic,
  onStep,
  onReset,
}: Props) {
  return (
    <aside className="w-56 min-w-[220px] bg-[#0D2137] flex flex-col py-5 px-3 overflow-y-auto">
      {/* Logo */}
      <div className="px-2 pb-4 mb-2 border-b border-slate-700 flex items-center justify-between">
        <Link href="/" className="text-lg font-bold text-white">
          🩺 <span className="text-blue-400">GEMA</span>-MED
        </Link>
        <UserButton afterSignOutUrl="/" />
      </div>

      {/* Topics */}
      <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-500 px-2 mt-3 mb-2">
        Tema
      </p>
      <div className="flex flex-col gap-0.5">
        {TOPICS.map((t) => (
          <button
            key={t.code}
            onClick={() => onTopic(activeTopic === t.code ? null : t.code)}
            className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-sm text-left transition-all ${
              activeTopic === t.code
                ? "bg-blue-600 text-white font-semibold"
                : "text-slate-400 hover:bg-slate-700/60 hover:text-white"
            }`}
          >
            <span>{t.emoji}</span>
            <span className="truncate">{t.label}</span>
          </button>
        ))}
      </div>

      {/* Steps */}
      <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-500 px-2 mt-4 mb-2">
        Step
      </p>
      <div className="flex gap-1.5 px-1">
        {[1, 2, 3].map((s) => (
          <button
            key={s}
            onClick={() => onStep(activeStep === s ? null : s)}
            className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeStep === s
                ? "bg-blue-600 text-white"
                : "bg-slate-700/50 text-slate-400 hover:bg-slate-700 hover:text-white"
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Progress */}
      <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-500 px-2 mt-5 mb-2">
        Progreso
      </p>
      <ProgressPanel data={progress} />

      {/* Links */}
      <div className="mt-auto pt-4 border-t border-slate-700 space-y-1">
        <Link
          href="/progress"
          className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-slate-700/60 transition-all"
        >
          📊 <span>Ver progreso completo</span>
        </Link>
        <button
          onClick={onReset}
          className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-sm text-slate-500 hover:text-red-400 hover:bg-red-900/20 transition-all"
        >
          ↺ <span>Nueva sesión</span>
        </button>
      </div>
    </aside>
  );
}
