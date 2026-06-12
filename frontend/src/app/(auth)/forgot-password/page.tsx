'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useTranslations } from 'next-intl';
import { useSettingStore } from '@/store/settingStore';
import { LoginCharacters } from "@/components/ui/login-characters";

export default function ForgotPasswordPage() {
  const t = useTranslations('Auth');
  const { setLocale } = useSettingStore();
  const [isTyping, setIsTyping] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // In a real app, logic would go here.
    alert('Reset link sent to your email!');
    window.location.href = '/login';
  };

  return (
    <div className="bg-background min-h-screen w-full flex flex-col items-center justify-center p-lg relative overflow-hidden font-body-md text-on-surface">
      {/* Decorative Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0 flex justify-center items-center">
        <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-primary/10 rounded-full blur-[100px] opacity-60"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-primary/5 rounded-full blur-[120px] opacity-40"></div>
      </div>

      {/* Split Card Container */}
      <main className="w-full max-w-[950px] bg-card-bg rounded-2xl shadow-modal flex overflow-hidden border border-outline-variant relative z-10 min-h-[500px]">

        {/* Left Side: Animation (Hidden on mobile) */}
        <div className="hidden lg:flex flex-1 bg-gradient-to-br from-primary/95 via-primary to-primary/90 relative overflow-hidden items-center justify-center p-8">
          <div className="scale-[0.75] origin-center transform-gpu">
            <LoginCharacters
              isTyping={isTyping}
              passwordLength={0}
              showPassword={false}
              brandName="TianTing"
            />
          </div>

          {/* Decorative overlay for the characters section */}
          <div className="absolute inset-0 bg-grid-white/[0.05] bg-[size:20px_20px] pointer-events-none" />
        </div>

        {/* Right Side: Forgot Password Form */}
        <div className="flex-1 p-10 lg:p-12 flex flex-col justify-center bg-card-bg">
          {/* Header Area */}
          <header className="flex flex-col items-center gap-sm text-center mb-8">
            <div className="bg-primary-container rounded-2xl flex items-center justify-center text-primary shadow-soft border border-primary/20 w-20 h-20 mb-2">
              <span className="material-symbols-outlined" style={{ fontSize: '52px', fontVariationSettings: "'FILL' 1" }}>smart_toy</span>
            </div>
            <h1 className="font-h1 text-3xl text-on-surface m-0 tracking-tight font-bold">{t('resetPassword')}</h1>
          </header>

          {/* Form */}
          <form className="flex flex-col gap-6" onSubmit={handleSubmit}>
            <div className="flex flex-col gap-2">
              <label className="font-label-sm text-sm text-on-surface-variant font-bold" htmlFor="email">{t('email')}</label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline-variant select-none pointer-events-none" style={{ fontSize: '20px' }}>mail</span>
                <input
                  id="email"
                  name="email"
                  className="w-full bg-surface-bg border border-outline-variant rounded-lg pl-10 pr-4 py-3 font-body-md text-on-surface placeholder:text-on-surface-variant/50 placeholder:font-bold focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all duration-200"
                  placeholder={t('placeholderEmail')}
                  type="email"
                  required
                  onFocus={() => setIsTyping(true)}
                  onBlur={() => setIsTyping(false)}
                  autoComplete="off"
                />
              </div>
            </div>

            <button
              className="w-full bg-primary hover:bg-primary-container text-on-primary font-bold py-3 rounded-lg shadow-soft hover:shadow-modal hover:-translate-y-[1px] transition-all duration-200 flex items-center justify-center gap-2"
              type="submit"
            >
              {t('sendLink')}
              <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>send</span>
            </button>
          </form>

          {/* Back Link */}
          <div className="mt-8 pt-6 border-t border-outline-variant text-center">
            <Link
              className="inline-flex items-center justify-center gap-2 font-bold text-primary hover:text-primary-container transition-colors duration-200"
              href="/login"
            >
              <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>arrow_back</span>
              {t('backToLogin')}
            </Link>
          </div>
        </div>
      </main>

      {/* Page Footer / Language Switcher */}
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
