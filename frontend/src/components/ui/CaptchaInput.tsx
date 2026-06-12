'use client';

import { useEffect, useState, useCallback, forwardRef, useImperativeHandle, useRef } from 'react';
import { authApi } from '@/lib/api';

export interface CaptchaInputHandle {
  fetchCaptcha: () => void;
}

interface CaptchaInputProps {
  value: string;
  onChange: (value: string) => void;
  captchaId: string;
  onCaptchaIdChange: (id: string) => void;
}

const CaptchaInput = forwardRef<CaptchaInputHandle, CaptchaInputProps>(
  function CaptchaInput({ value, onChange, captchaId, onCaptchaIdChange }, ref) {
    const [captchaImage, setCaptchaImage] = useState('');
    const [loading, setLoading] = useState(false);
    const mountedRef = useRef(false);

    const fetchCaptcha = useCallback(async () => {
      setLoading(true);
      try {
        const res: any = await authApi.getCaptcha();
        if (res?.data?.captchaId && res?.data?.captchaImage) {
          onCaptchaIdChange(res.data.captchaId);
          setCaptchaImage(res.data.captchaImage);
          onChange('');
        }
      } catch {
        // silent fail
      } finally {
        setLoading(false);
      }
    }, [onCaptchaIdChange, onChange]);

    useImperativeHandle(ref, () => ({
      fetchCaptcha,
    }), [fetchCaptcha]);

    useEffect(() => {
      if (!mountedRef.current) {
        mountedRef.current = true;
        fetchCaptcha();
      }
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    return (
      <div className="flex gap-2 items-center">
        <div className="w-[120px] h-[44px] bg-surface-bg rounded-lg border border-outline-variant overflow-hidden flex-shrink-0">
          {captchaImage ? (
            <img
              src={captchaImage}
              alt="captcha"
              className="w-full h-full object-cover cursor-pointer"
              onClick={fetchCaptcha}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-on-surface-variant">
              {loading ? '...' : 'N/A'}
            </div>
          )}
        </div>
        <input
          className="flex-1 px-4 py-2.5 bg-surface-bg rounded-lg border border-outline-variant focus:border-primary focus:ring-2 focus:ring-primary/20 font-body-md text-on-surface placeholder:text-on-surface-variant/50 placeholder:font-bold transition-all outline-none"
          placeholder="验证码"
          type="text"
          maxLength={4}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
        <button
          type="button"
          className="flex-shrink-0 w-9 h-9 flex items-center justify-center text-outline-variant hover:text-primary transition-colors"
          onClick={fetchCaptcha}
          disabled={loading}
        >
          <span className="material-symbols-outlined" style={{ fontSize: '22px' }}>refresh</span>
        </button>
      </div>
    );
  }
);

export { CaptchaInput };
export default CaptchaInput;