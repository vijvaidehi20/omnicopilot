import { useState } from 'react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import ThemeToggle from '../components/ThemeToggle';
import { Sparkles, Mail, Lock, ArrowRight, Loader2 } from 'lucide-react';

export default function LoginPage() {
  const { isDark } = useTheme();
  const { login, signup } = useAuth();

  const [isSignup, setIsSignup] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isSignup) {
        await signup(email, password);
      } else {
        await login(email, password);
      }
    } catch (err) {
      const msg = err.response?.data?.detail || 'Something went wrong';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden"
      style={{
        background: isDark
          ? 'radial-gradient(ellipse at 50% 0%, rgba(99,102,241,0.12) 0%, #0b0f1a 60%)'
          : 'radial-gradient(ellipse at 50% 0%, rgba(99,102,241,0.08) 0%, #f8fafc 60%)',
      }}
    >
      {/* Theme toggle - top right */}
      <div className="absolute top-5 right-5">
        <ThemeToggle />
      </div>

      {/* Decorative orbs */}
      <div
        className="absolute w-72 h-72 rounded-full opacity-20 blur-3xl"
        style={{
          background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
          top: '-5%',
          left: '20%',
        }}
      />
      <div
        className="absolute w-96 h-96 rounded-full opacity-10 blur-3xl"
        style={{
          background: 'linear-gradient(135deg, #06b6d4, #6366f1)',
          bottom: '-10%',
          right: '10%',
        }}
      />

      {/* Login card */}
      <div
        className="relative w-full max-w-md animate-fade-in"
        style={{ animationDuration: '0.6s' }}
      >
        <div
          className="glass rounded-2xl p-8 space-y-6"
          style={{
            boxShadow: isDark
              ? '0 25px 60px rgba(0,0,0,0.5), 0 0 40px rgba(99,102,241,0.08)'
              : '0 25px 60px rgba(0,0,0,0.08), 0 0 40px rgba(99,102,241,0.05)',
          }}
        >
          {/* Logo */}
          <div className="text-center space-y-3">
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto animate-pulse-glow"
              style={{
                background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              }}
            >
              <Sparkles size={26} className="text-white" />
            </div>
            <div>
              <h1
                className="text-2xl font-bold tracking-tight"
                style={{ color: isDark ? '#f1f5f9' : '#1e293b' }}
              >
                OmniCopilot
              </h1>
              <p
                className="text-sm mt-1"
                style={{ color: isDark ? '#64748b' : '#94a3b8' }}
              >
                {isSignup ? 'Create your account' : 'Welcome back'}
              </p>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div
              className="text-sm px-4 py-3 rounded-xl animate-fade-in"
              style={{
                background: 'rgba(239,68,68,0.1)',
                border: '1px solid rgba(239,68,68,0.2)',
                color: '#ef4444',
              }}
            >
              {error}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium" style={{ color: isDark ? '#94a3b8' : '#64748b' }}>
                Email
              </label>
              <div className="relative">
                <Mail
                  size={16}
                  className="absolute left-3 top-1/2 -translate-y-1/2"
                  style={{ color: isDark ? '#475569' : '#94a3b8' }}
                />
                <input
                  id="email-input"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="you@example.com"
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl text-sm outline-none transition-all duration-200 focus:ring-2 focus:ring-primary-500/30"
                  style={{
                    background: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.03)',
                    border: isDark ? '1px solid rgba(255,255,255,0.08)' : '1px solid rgba(0,0,0,0.08)',
                    color: isDark ? '#e2e8f0' : '#1e293b',
                  }}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium" style={{ color: isDark ? '#94a3b8' : '#64748b' }}>
                Password
              </label>
              <div className="relative">
                <Lock
                  size={16}
                  className="absolute left-3 top-1/2 -translate-y-1/2"
                  style={{ color: isDark ? '#475569' : '#94a3b8' }}
                />
                <input
                  id="password-input"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl text-sm outline-none transition-all duration-200 focus:ring-2 focus:ring-primary-500/30"
                  style={{
                    background: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.03)',
                    border: isDark ? '1px solid rgba(255,255,255,0.08)' : '1px solid rgba(0,0,0,0.08)',
                    color: isDark ? '#e2e8f0' : '#1e293b',
                  }}
                />
              </div>
            </div>

            <button
              id="submit-btn"
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold text-white transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-60 disabled:hover:scale-100 cursor-pointer"
              style={{
                background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
                boxShadow: '0 4px 20px rgba(99,102,241,0.35)',
              }}
            >
              {loading ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <>
                  {isSignup ? 'Create Account' : 'Sign In'}
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          {/* Google Auth */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" style={{ borderColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)' }}></span>
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="px-2" style={{ background: isDark ? '#141b2d' : '#ffffff', color: isDark ? '#64748b' : '#94a3b8' }}>Or continue with</span>
            </div>
          </div>

          <button
            id="google-login-btn"
            type="button"
            onClick={() => {
              window.location.href = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/auth/google/login`;
            }}
            className="w-full flex items-center justify-center gap-3 py-3 rounded-xl text-sm font-medium transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] cursor-pointer shadow-sm"
            style={{
              background: isDark ? 'rgba(255,255,255,0.03)' : '#ffffff',
              border: isDark ? '1px solid rgba(255,255,255,0.1)' : '1px solid #e2e8f0',
              color: isDark ? '#e2e8f0' : '#475569',
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-1 .67-2.28 1.07-3.71 1.07-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
              <path d="M5.84 14.11c-.22-.66-.35-1.36-.35-2.11s.13-1.45.35-2.11V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l3.66-2.83z" fill="#FBBC05" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.53 12-4.53z" fill="#EA4335" />
            </svg>
            Sign in with Google
          </button>

          {/* Toggle signup/login */}
          <p className="text-center text-sm" style={{ color: isDark ? '#64748b' : '#94a3b8' }}>
            {isSignup ? 'Already have an account?' : "Don't have an account?"}{' '}
            <button
              id="toggle-auth-mode"
              onClick={() => { setIsSignup(!isSignup); setError(''); }}
              className="font-semibold transition-colors duration-200 cursor-pointer"
              style={{ color: '#818cf8' }}
            >
              {isSignup ? 'Sign In' : 'Sign Up'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
