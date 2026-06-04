import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="text-4xl mb-3">🩺</div>
          <h1 className="text-2xl font-bold text-slate-900">Bienvenido de vuelta</h1>
          <p className="text-slate-500 text-sm mt-1">Inicia sesión para continuar estudiando</p>
        </div>
        <SignIn />
      </div>
    </div>
  );
}
