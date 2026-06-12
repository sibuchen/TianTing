'use client';

import React, { useState, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useSettingStore } from '@/store/settingStore';
import { useAuthStore } from '@/store/authStore';
import { LoginCharacters } from "@/components/ui/login-characters";
import { FluidDropdown } from '@/components/ui/fluid-dropdown';
import { CaptchaInput, CaptchaInputHandle } from '@/components/ui/CaptchaInput';
import { authApi } from '@/lib/api';
import { Phone } from 'lucide-react';

export default function RegisterPage() {
  const t = useTranslations('Auth');
  const router = useRouter();
  const { setLocale } = useSettingStore();
  const { setUser } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [captchaId, setCaptchaId] = useState('');
  const [formData, setFormData] = useState({
    email: '',
    phone: '',
    phonePrefix: '+86',
    code: '',
    password: '',
    confirmPassword: '',
    captchaCode: '',
    agreeTerms: false
  });

  const captchaRef = useRef<CaptchaInputHandle>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('两次密码输入不一致');
      return;
    }

    if (formData.password.length < 8) {
      setError('密码至少需要8位');
      return;
    }

    const phonePattern = /^1[3-9]\d{9}$/;
    if (!phonePattern.test(formData.phone)) {
      setError('手机号格式不正确');
      return;
    }

    if (!formData.captchaCode || formData.captchaCode.length !== 4) {
      setError('请输入验证码');
      return;
    }

    setLoading(true);
    try {
      const response: any = await authApi.register({
        username: formData.email.split('@')[0],
        email: formData.email,
        password: formData.password,
        phone: formData.phone,
        captchaId: captchaId,
        captchaCode: formData.captchaCode || '',
      });

      if (response.user) {
        setUser(response.user);
        const redirectPath = response.user?.role === 'operator' ? '/human-service' : '/dashboard';
        window.location.href = redirectPath;
      }
    } catch (err: any) {
      const message = err?.response?.data?.message || err?.response?.data?.detail || '注册失败，请重试';
      setError(message);
      captchaRef.current?.fetchCaptcha();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-background min-h-screen w-full flex flex-col items-center justify-center p-lg relative overflow-hidden font-body-md text-on-surface">
      {/* Decorative Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0 flex justify-center items-center">
        <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-primary/10 rounded-full blur-[100px] opacity-60"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-primary/5 rounded-full blur-[120px] opacity-40"></div>
      </div>

      {/* Split Card Container */}
      <main className="w-full max-w-[950px] bg-card-bg rounded-2xl shadow-modal flex overflow-hidden border border-outline-variant relative z-10 min-h-[650px]">

        {/* Left Side: Animation (Hidden on mobile) */}
        <div className="hidden lg:flex flex-1 bg-gradient-to-br from-primary/95 via-primary to-primary/90 relative overflow-hidden items-center justify-center p-8">
          <div className="scale-[0.75] origin-center transform-gpu">
            <LoginCharacters
              isTyping={isTyping}
              passwordLength={formData.password.length}
              showPassword={showPassword}
              brandName="TianTing"
            />
          </div>

          {/* Decorative overlay for the characters section */}
          <div className="absolute inset-0 bg-grid-white/[0.05] bg-[size:20px_20px] pointer-events-none" />
        </div>

        {/* Right Side: Registration Form */}
        <div className="flex-1 p-10 lg:p-12 flex flex-col justify-center bg-card-bg overflow-y-auto">
          {/* Header Area */}
          <header className="flex flex-col items-center gap-sm text-center mb-8">
            <div className="bg-primary-container rounded-2xl flex items-center justify-center text-primary shadow-soft border border-primary/20 w-20 h-20 mb-2">
              <span className="material-symbols-outlined" style={{ fontSize: '52px' }}>headset_mic</span>
            </div>
            <h1 className="font-h1 text-3xl text-on-surface m-0 tracking-tight font-bold">TianTing</h1>
          </header>

          {/* Registration Form */}
          <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
            {/* Email Input */}
            <div className="flex flex-col gap-1.5">
              <label className="font-label-sm text-xs text-on-surface-variant font-bold" htmlFor="email">{t('email')}</label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline-variant" style={{ fontSize: '20px' }}>mail</span>
                <input
                  className="w-full pl-10 pr-4 py-2.5 bg-surface-bg rounded-lg border border-outline-variant focus:border-primary focus:ring-2 focus:ring-primary/20 font-body-md text-on-surface placeholder:text-on-surface-variant/50 placeholder:font-bold transition-all outline-none"
                  id="email"
                  placeholder={t('placeholderEmail')}
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  onFocus={() => setIsTyping(true)}
                  onBlur={() => setIsTyping(false)}
                  autoComplete="off"
                />
              </div>
            </div>

            {/* Phone Input */}
            <div className="flex flex-col gap-1.5">
              <label className="font-label-sm text-xs text-on-surface-variant font-bold" htmlFor="phone">{t('phone')}</label>
              <div className="flex">
                <FluidDropdown
                  value={formData.phonePrefix}
                  onChange={(val) => setFormData({ ...formData, phonePrefix: val })}
                  className="w-24 shrink-0"
                  options={[
                    { id: '+86', label: '+86', icon: Phone, color: '#FF6B6B' },
                    { id: '+1', label: '+1', icon: Phone, color: '#45B7D1' },
                    { id: '+44', label: '+44', icon: Phone, color: '#4ECDC4' },
                  ]}
                />
                <input
                  id="phone"
                  className="flex-1 ml-2 px-4 py-2.5 bg-surface-bg rounded-lg border border-outline-variant focus:border-primary focus:ring-2 focus:ring-primary/20 font-body-md text-on-surface placeholder:text-on-surface-variant/50 placeholder:font-bold transition-all outline-none"
                  placeholder={t('phone')}
                  type="tel"
                  required
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  onFocus={() => setIsTyping(true)}
                  onBlur={() => setIsTyping(false)}
                />
              </div>
            </div>

            {/* Verification Code */}
            <div className="flex flex-col gap-1.5">
              <label className="font-label-sm text-xs text-on-surface-variant font-bold" htmlFor="code">{t('verificationCode')}</label>
              <div className="flex gap-2">
                <input
                  id="code"
                  className="flex-1 px-4 py-2.5 bg-surface-bg rounded-lg border border-outline-variant focus:border-primary focus:ring-2 focus:ring-primary/20 font-body-md text-on-surface placeholder:text-on-surface-variant/50 placeholder:font-bold transition-all outline-none"
                  placeholder={t('verificationCode')}
                  type="text"
                  required
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  onFocus={() => setIsTyping(true)}
                  onBlur={() => setIsTyping(false)}
                />
                <button
                  className="px-4 py-2.5 bg-surface-bg border border-primary text-primary rounded-lg font-bold text-xs hover:bg-primary-container transition-colors whitespace-nowrap active:scale-95"
                  type="button"
                >
                  {t('getVerificationCode')}
                </button>
              </div>
            </div>

            {/* Password Input */}
            <div className="flex flex-col gap-1.5">
              <label className="font-label-sm text-xs text-on-surface-variant font-bold" htmlFor="password">{t('password')}</label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline-variant" style={{ fontSize: '20px' }}>lock</span>
                <input
                  className="w-full pl-10 pr-10 py-2.5 bg-surface-bg border border-outline-variant rounded-lg font-body-md text-on-surface placeholder:text-on-surface-variant/50 placeholder:font-bold focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all duration-200"
                  id="password"
                  placeholder={t('passwordPlaceholder')}
                  type={showPassword ? "text" : "password"}
                  required
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  onFocus={() => setIsTyping(true)}
                  onBlur={() => setIsTyping(false)}
                />
                <button
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-outline-variant hover:text-on-surface transition-colors flex items-center justify-center"
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>
                    {showPassword ? 'visibility' : 'visibility_off'}
                  </span>
                </button>
              </div>
            </div>

            {/* Confirm Password */}
            <div className="flex flex-col gap-1.5">
              <label className="font-label-sm text-xs text-on-surface-variant font-bold" htmlFor="confirmPassword">{t('confirmPassword')}</label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline-variant" style={{ fontSize: '20px' }}>lock</span>
                <input
                  className="w-full pl-10 pr-10 py-2.5 bg-surface-bg border border-outline-variant rounded-lg font-body-md text-on-surface placeholder:text-on-surface-variant/50 placeholder:font-bold focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all duration-200"
                  id="confirmPassword"
                  placeholder={t('placeholderConfirmPassword')}
                  type={showPassword ? "text" : "password"}
                  required
                  value={formData.confirmPassword}
                  onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                  onFocus={() => setIsTyping(true)}
                  onBlur={() => setIsTyping(false)}
                />
                <button
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-outline-variant hover:text-on-surface transition-colors flex items-center justify-center"
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>
                    {showPassword ? 'visibility' : 'visibility_off'}
                  </span>
                </button>
              </div>
            </div>

            {/* Terms and Conditions */}
            <div className="flex items-start gap-2 py-1">
              <input
                id="terms"
                className="w-4 h-4 mt-0.5 text-primary bg-surface-bg border-outline-variant rounded focus:ring-primary/20 cursor-pointer"
                type="checkbox"
                required
                checked={formData.agreeTerms}
                onChange={(e) => setFormData({ ...formData, agreeTerms: e.target.checked })}
              />
              <label className="font-body-sm text-xs text-on-surface-variant leading-relaxed" htmlFor="terms">
                {t('termsText')} <Link className="text-primary hover:underline" href="#">{t('serviceAgreement')}</Link> {t('and')} <Link className="text-primary hover:underline" href="#">{t('privacyPolicy')}</Link>
              </label>
            </div>

            {/* Captcha */}
            <div className="flex flex-col gap-1.5">
              <CaptchaInput
                ref={captchaRef}
                value={formData.captchaCode || ''}
                onChange={(val) => setFormData({ ...formData, captchaCode: val })}
                captchaId={captchaId}
                onCaptchaIdChange={setCaptchaId}
              />
            </div>

            {/* Error Display */}
            {error && (
              <div className="bg-error/10 border border-error/30 text-error rounded-lg px-4 py-3 font-body-sm text-sm">
                {error}
              </div>
            )}

            {/* Submit Button */}
            <button
              className="mt-2 w-full bg-primary hover:bg-primary-container text-on-primary font-bold py-2.5 rounded-lg shadow-soft hover:shadow-modal hover:-translate-y-[1px] transition-all duration-200 flex items-center justify-center gap-2"
              type="submit"
              disabled={loading}
            >
              {loading ? '注册中...' : t('registerNow')}
              {!loading && <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>rocket_launch</span>}
            </button>
          </form>

          <div className="text-center mt-6">
            <p className="font-body-md text-sm text-on-surface-variant font-bold">
              {t('alreadyHaveAccount')}
              <Link className="text-primary hover:text-primary-container transition-colors ml-1 font-bold" href="/login">{t('loginNow')}</Link>
            </p>
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
