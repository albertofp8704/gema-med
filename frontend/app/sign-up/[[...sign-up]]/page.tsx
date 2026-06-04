import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="text-4xl mb-3">🩺</div>
          <h1 className="text-2xl font-bold text-slate-900">Crear cuenta</h1>
          <p className="text-slate-500 text-sm mt-1">Empieza a prepararte para el USMLE hoy</p>
        </div>
        <SignUp />
      </div>
    </div>
  );
}
