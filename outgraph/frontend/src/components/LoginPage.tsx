import React, { useState } from 'react';
import { ShieldCheck, Lock, User, AlertCircle } from 'lucide-react';

interface LoginPageProps {
  onLoginSuccess: (user: { id: string; role: string }) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [officialId, setOfficialId] = useState('ISRO-SCI-8842');
  const [password, setPassword] = useState('••••••••••••');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    setTimeout(() => {
      if (officialId.trim() !== '') {
        onLoginSuccess({
          id: officialId,
          role: 'Authorized Official',
        });
      } else {
        setError('Please enter a valid ISRO Official Scientist ID.');
      }
      setIsLoading(false);
    }, 500);
  };

  const handleDemoLogin = (id: string) => {
    setOfficialId(id);
    setPassword('ISRO-LUNAR-2026');
    setTimeout(() => {
      onLoginSuccess({
        id: id,
        role: 'Authorized Official',
      });
    }, 300);
  };

  return (
    <div className="min-h-screen w-full bg-[#0d2247] flex flex-col justify-between items-center relative overflow-hidden font-sans">
      {/* Background Grid Pattern */}
      <div 
        className="absolute inset-0 opacity-15 pointer-events-none"
        style={{
          backgroundImage: `radial-gradient(circle at 1px 1px, rgba(255,255,255,0.3) 1px, transparent 0)`,
          backgroundSize: '24px 24px'
        }}
      />

      {/* Top ISRO Banner & Header */}
      <div className="w-full flex flex-col items-center pt-8 z-10 px-4 text-center">
        <div className="w-24 h-20 mb-3 bg-white p-2 rounded-2xl shadow-xl border border-orange-400 flex items-center justify-center">
          <img 
            src="/isro_logo.jpg" 
            alt="ISRO Logo" 
            className="w-full h-full object-contain rounded-lg"
            onError={(e) => {
              (e.target as HTMLElement).style.display = 'none';
            }}
          />
        </div>
        <h1 className="text-white text-lg font-bold tracking-widest uppercase">
          ISRO SECURE ACCESS PROTOTYPE
        </h1>
        <p className="text-blue-200 text-xs mt-1 tracking-wide font-medium">
          Indian Space Research Organisation — Department of Space (ISRO)
        </p>
      </div>

      {/* Login Card */}
      <div className="w-full max-w-md z-10 px-4 my-auto">
        <div className="bg-white rounded-2xl shadow-2xl overflow-hidden border border-slate-200 relative">
          {/* Top Tricolor Strip Header */}
          <div className="h-1.5 w-full flex">
            <div className="h-full w-1/3 bg-[#FF9933]" />
            <div className="h-full w-1/3 bg-white" />
            <div className="h-full w-1/3 bg-[#138808]" />
          </div>

          <div className="p-8">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-extrabold text-[#0d2247] tracking-tight">
                LunarSynapse
              </h2>
              <p className="text-slate-500 text-xs mt-0.5 font-medium">
                ISRO Authorized Official Portal
              </p>
            </div>

            {/* Demo Notice Box */}
            <div className="mb-6 p-3.5 bg-amber-50 border border-amber-200 rounded-xl text-left">
              <div className="flex items-center space-x-1.5 text-amber-800 font-bold text-xs">
                <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
                <span>DEMO PROTOTYPE — Credentials below are for testing only.</span>
              </div>
              <div className="mt-2.5 flex space-x-3 text-xs font-semibold">
                <button
                  type="button"
                  onClick={() => handleDemoLogin('ISRO-SCI-8842')}
                  className="text-blue-700 hover:underline"
                >
                  Use Official Demo Login
                </button>
                <span className="text-slate-300">|</span>
                <button
                  type="button"
                  onClick={() => handleDemoLogin('ISRO-ADMIN-001')}
                  className="text-blue-700 hover:underline"
                >
                  Use Admin Demo Login
                </button>
              </div>
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-xs flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  OFFICIAL ID
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <User className="w-4 h-4" />
                  </div>
                  <input
                    type="text"
                    required
                    value={officialId}
                    onChange={(e) => setOfficialId(e.target.value)}
                    placeholder="e.g. ISRO-SCI-8842"
                    className="w-full pl-9 pr-3 py-2.5 bg-blue-50/50 border border-blue-100 rounded-lg text-sm text-slate-800 font-semibold focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  PASSWORD
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-9 pr-3 py-2.5 bg-blue-50/50 border border-blue-100 rounded-lg text-sm text-slate-800 font-semibold focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white transition-all"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full mt-2 py-3 px-4 bg-[#0d2247] hover:bg-blue-900 text-white font-bold text-sm rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 flex items-center justify-center space-x-2 active:scale-[0.99]"
              >
                {isLoading ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    <span>SECURE LOGIN</span>
                  </>
                )}
              </button>
            </form>

            <div className="mt-6 text-center border-t border-slate-100 pt-4">
              <p className="text-[10px] text-slate-400 font-medium">
                LunarSynapse Secure Access Prototype • Not a real ISRO system
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="w-full pb-4 text-center z-10 text-[11px] text-blue-200 opacity-80 font-medium">
        Multi-modal, Sun-angle and Scale Invariant Image Correspondence using Chandrayaan-2 OHRC, TMC-2 and IIRS
      </div>
    </div>
  );
};
