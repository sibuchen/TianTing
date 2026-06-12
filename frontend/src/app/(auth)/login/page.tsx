'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useTranslations } from 'next-intl';
import { useRouter } from 'next/navigation';
import { useSettingStore } from '@/store/settingStore';
import { useAuthStore } from '@/store/authStore';
import { authApi } from '@/lib/api';
import { LoginCharacters } from "@/components/ui/login-characters";

export default function LoginPage() {
  const t = useTranslations('Auth');
  const router = useRouter();
  const { setLocale } = useSettingStore();
  const { setUser } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response: any = await authApi.login({ username, password, remember });
      if (response.user) {
        setUser(response.user);
        const redirectPath = response.user?.role === 'operator' ? '/human-service' : '/dashboard';
        router.push(redirectPath);
      }
    } catch (err: any) {
      const message = err?.response?.data?.message || t('loginFailed');
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-background min-h-screen w-full flex flex-col items-center justify-center p-lg relative overflow-hidden font-body-md text-on-surface">
      {/* Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0 flex justify-center items-center">
        <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-primary/10 rounded-full blur-[100px] opacity-60"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-primary/5 rounded-full blur-[120px] opacity-40"></div>
      </div>

      {/* Split Card Container */}
      <main className="w-full max-w-[950px] bg-card-bg rounded-2xl shadow-modal flex overflow-hidden border border-outline-variant relative z-10 min-h-[600px]">

        {/* Left Side: Animation (Hidden on mobile) */}
        <div className="hidden lg:flex flex-1 bg-gradient-to-br from-primary/95 via-primary to-primary/90 relative overflow-hidden items-center justify-center p-8">
          <div className="scale-[0.75] origin-center transform-gpu">
            <LoginCharacters
              isTyping={isTyping}
              passwordLength={password.length}
              showPassword={showPassword}
              brandName="TianTing"
            />
          </div>

          {/* Decorative overlay for the characters section */}
          <div className="absolute inset-0 bg-grid-white/[0.05] bg-[size:20px_20px] pointer-events-none" />
        </div>

        {/* Right Side: Login Form */}
        <div className="flex-1 p-10 lg:p-12 flex flex-col justify-center bg-card-bg">
          {/* Header Area */}
          <header className="flex flex-col items-center gap-sm text-center mb-8">
            <div className="bg-primary-container rounded-2xl flex items-center justify-center text-primary shadow-soft border border-primary/20 w-20 h-20 mb-2">
              <span className="material-symbols-outlined" style={{ fontSize: '52px' }}>support_agent</span>
            </div>
            <h1 className="font-h1 text-3xl text-on-surface m-0 tracking-tight font-bold">TianTing</h1>
          </header>

          {/* Login Form */}
          <form className="flex flex-col gap-5" onSubmit={handleSubmit}>
            {/* Username Input */}
            <div className="flex flex-col gap-2">
              <label className="font-label-sm text-sm text-on-surface-variant font-bold" htmlFor="username">{t('emailOrUsername')}</label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline-variant" style={{ fontSize: '20px' }}>person</span>
                <input
                  className="w-full pl-10 pr-4 py-3 bg-surface-bg rounded-lg border border-outline-variant focus:border-primary focus:ring-2 focus:ring-primary/20 font-body-md text-on-surface placeholder:text-on-surface-variant/50 placeholder:font-bold transition-all outline-none"
                  id="username"
                  placeholder={t('placeholderEmail')}
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  onFocus={() => setIsTyping(true)}
                  onBlur={() => setIsTyping(false)}
                  autoComplete="off"
                />
              </div>
            </div>

            {/* Password Input */}
            <div className="flex flex-col gap-2">
              <div className="flex justify-between items-center">
                <label className="font-label-sm text-sm text-on-surface-variant font-bold" htmlFor="password">{t('password')}</label>
                <Link className="font-label-sm text-xs text-primary hover:text-primary-container transition-colors font-bold" href="/forgot-password">{t('forgotPassword')}</Link>
              </div>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline-variant" style={{ fontSize: '20px' }}>lock</span>
                <input
                  className="w-full pl-10 pr-10 py-3 bg-surface-bg border border-outline-variant rounded-lg font-body-md text-on-surface placeholder:text-on-surface-variant/50 placeholder:font-bold focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all duration-200"
                  id="password"
                  placeholder={t('placeholderPassword')}
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onFocus={() => setIsTyping(true)}
                  onBlur={() => setIsTyping(false)}
                />
                <button
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-outline-variant hover:text-on-surface transition-colors flex items-center justify-center"
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: '22px' }}>
                    {showPassword ? 'visibility' : 'visibility_off'}
                  </span>
                </button>
              </div>
            </div>

            {/* Remember Me */}
            <div className="flex items-center gap-2 mt-1">
              <input
                className="w-4 h-4 rounded border-outline-variant text-primary focus:ring-primary/20 bg-surface-bg cursor-pointer"
                id="remember"
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
              />
              <label className="font-body-sm text-sm text-on-surface-variant cursor-pointer font-bold" htmlFor="remember">{t('rememberMe')}</label>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-error/10 border border-error/30 text-error rounded-lg px-4 py-3 font-body-sm text-sm">
                {error}
              </div>
            )}

            {/* Submit Button */}
            <button
              className="mt-4 w-full bg-primary hover:bg-primary-container text-on-primary font-bold py-3 rounded-lg shadow-soft hover:shadow-modal hover:-translate-y-[1px] transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              type="submit"
              disabled={loading}
            >
              {loading ? t('signingIn') : t('signIn')}
              {!loading && <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>arrow_forward</span>}
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-3 my-6">
            <div className="h-px bg-outline-variant flex-1 opacity-40"></div>
            <span className="font-label-sm text-xs text-outline-variant uppercase tracking-wider font-bold">{t('orContinueWith')}</span>
            <div className="h-px bg-outline-variant flex-1 opacity-40"></div>
          </div>

          {/* SSO Button */}
          <button className="w-full bg-surface-bg border border-outline-variant hover:bg-surface-container-high text-on-surface font-bold py-3 rounded-lg transition-all duration-200 flex items-center justify-center gap-2" type="button">
            <span className="material-symbols-outlined" style={{ fontSize: '22px' }}>business_center</span>
            {t('corporateSso')}
          </button>

          <div className="text-center mt-8">
            <p className="font-body-md text-sm text-on-surface-variant font-bold">
              {t('noAccount')}
              <Link className="text-primary hover:text-primary-container transition-colors ml-1 font-bold" href="/register">{t('registerNow')}</Link>
            </p>
          </div>
        </div>
      </main>

      {/* Footer / Language Switcher */}
      <footer className="mt-8 flex flex-col items-center gap-1 text-center z-10">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setLocale('en')}
            className="font-label-sm text-sm text-on-surface-variant hover:text-primary transition-colors font-bold"
          >
            English
          </button>
          <span className="w-1.5 h-1.5 rounded-full bg-outline-variant"></span>
          <button
            onClick={() => setLocale('zh')}
            className="font-label-sm text-sm text-on-surface-variant hover:text-primary transition-colors font-bold"
          >
            简体中文
          </button>
        </div>
        <p className="font-body-sm text-xs text-outline-variant mt-1">{t('footer')}</p>
      </footer>
    </div>
  );
}
