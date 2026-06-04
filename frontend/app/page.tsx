import Link from "next/link";
import { SignedIn, SignedOut, UserButton } from "@clerk/nextjs";

const features = [
  { emoji: "🎯", title: "12,723 preguntas reales", desc: "Banco MedQA — las mismas preguntas estilo USMLE usadas en investigación de IA médica." },
  { emoji: "🤖", title: "Explicaciones con Claude", desc: "Cada respuesta incluye fisiopatología, distractores y puntos high-yield, generados por Claude." },
  { emoji: "📊", title: "Tracking por tema y Step", desc: "Tu rendimiento en Cardio, Neuro, Farmaco... por Step 1/2/3. Ve dónde mejorar." },
  { emoji: "🔬", title: "Referencias PubMed reales", desc: "El tutor cita artículos peer-reviewed de PubMed en sus explicaciones." },
  { emoji: "💬", title: "También en Telegram", desc: "Accede desde el móvil vía bot de Telegram. Misma IA, mismo progreso." },
  { emoji: "🇨🇺", title: "Ruta ECFMG para cubanos", desc: "Guía específica para médicos cubanos: ECFMG, USMLE Steps, residency match." },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navbar */}
      <nav className="border-b border-slate-100 sticky top-0 bg-white/90 backdrop-blur z-50">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <span className="text-xl font-bold text-slate-900">
            🩺 <span className="text-blue-600">GEMA</span>-MED
          </span>
          <div className="flex items-center gap-4">
            <SignedOut>
              <Link
                href="/sign-in"
                className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
              >
                Iniciar sesión
              </Link>
              <Link
                href="/sign-up"
                className="text-sm font-semibold bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                Empezar gratis →
              </Link>
            </SignedOut>
            <SignedIn>
              <Link
                href="/study"
                className="text-sm font-semibold bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                Ir al tutor
              </Link>
              <UserButton afterSignOutUrl="/" />
            </SignedIn>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-6 pt-24 pb-16 text-center">
        <div className="inline-flex items-center gap-2 bg-blue-50 text-blue-700 text-xs font-semibold px-3 py-1.5 rounded-full mb-8 border border-blue-100">
          ✨ Powered by Claude · MedQA · PubMed
        </div>
        <h1 className="text-5xl font-bold text-slate-900 mb-6 leading-tight">
          Prepárate para el{" "}
          <span className="text-blue-600">USMLE</span>{" "}
          con IA
        </h1>
        <p className="text-xl text-slate-500 mb-10 max-w-2xl mx-auto leading-relaxed">
          Tutor médico con 12,723 preguntas reales, explicaciones con fisiopatología
          y tracking de progreso. Diseñado para médicos graduados en Cuba que buscan
          la reválida en USA.
        </p>
        <div className="flex items-center justify-center gap-4 flex-wrap">
          <Link
            href="/sign-up"
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-3.5 rounded-xl text-base transition-colors shadow-sm"
          >
            Empezar gratis →
          </Link>
          <Link
            href="/sign-in"
            className="text-slate-600 hover:text-slate-900 font-medium px-6 py-3.5 rounded-xl text-base transition-colors border border-slate-200 hover:border-slate-300"
          >
            Ya tengo cuenta
          </Link>
        </div>
      </section>

      {/* Badge row */}
      <section className="border-y border-slate-100 bg-slate-50">
        <div className="max-w-4xl mx-auto px-6 py-5 flex flex-wrap items-center justify-center gap-8 text-sm text-slate-500 font-medium">
          <span>✅ 12,723 preguntas USMLE</span>
          <span>✅ Step 1 · Step 2 CK · Step 3</span>
          <span>✅ ECFMG para IMGs</span>
          <span>✅ 100% gratuito</span>
          <span>✅ Sin límite de preguntas</span>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <h2 className="text-3xl font-bold text-center text-slate-900 mb-4">
          Todo lo que necesitas para pasar los boards
        </h2>
        <p className="text-center text-slate-500 mb-14 text-base">
          Sin costos de suscripción. Sin límites de preguntas. Solo estudia.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f) => (
            <div
              key={f.title}
              className="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="text-3xl mb-4">{f.emoji}</div>
              <h3 className="font-semibold text-slate-900 mb-2">{f.title}</h3>
              <p className="text-slate-500 text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-blue-600 py-16">
        <div className="max-w-2xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Empieza a estudiar ahora
          </h2>
          <p className="text-blue-100 mb-8 text-base">
            Crea tu cuenta en 30 segundos. Sin tarjeta de crédito.
          </p>
          <Link
            href="/sign-up"
            className="bg-white text-blue-600 font-bold px-8 py-3.5 rounded-xl text-base hover:bg-blue-50 transition-colors inline-block"
          >
            Crear cuenta gratis →
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-100 py-8">
        <div className="max-w-6xl mx-auto px-6 text-center text-sm text-slate-400">
          🩺 GEMA-MED · Tutor USMLE para médicos cubanos · Powered by{" "}
          <a href="https://anthropic.com" className="underline">Claude</a> y{" "}
          <a href="https://huggingface.co/datasets/bigbio/med_qa" className="underline">MedQA</a>
        </div>
      </footer>
    </div>
  );
}
