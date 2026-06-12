'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { authApi } from '@/lib/api';

const publicPaths = ['/login', '/register', '/forgot-password'];
const adminOnlyPaths = ['/dashboard', '/agents', '/skills', '/tools', '/knowledge', '/users', '/api-keys'];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { user, hydrate, setLoading, isAuthenticated, isLoading } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (publicPaths.some((p) => pathname?.startsWith(p))) {
      setLoading(false);
      return;
    }

    authApi.me()
      .then((res: any) => {
        if (res?.data) {
          hydrate(res.data);
        } else {
          setLoading(false);
        }
      })
      .catch(() => {
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (!isLoading && !isAuthenticated && !publicPaths.some((p) => pathname?.startsWith(p))) {
      router.push('/login');
    }
  }, [isLoading, isAuthenticated, pathname, router]);

  useEffect(() => {
    if (!isLoading && isAuthenticated && user?.role === 'operator') {
      const isAdminPath = adminOnlyPaths.some((p) => pathname?.startsWith(p));
      if (isAdminPath) {
        router.push('/human-service');
      }
    }
  }, [isLoading, isAuthenticated, user, pathname, router]);

  useEffect(() => {
    if (!isLoading && isAuthenticated && user?.role === 'admin' && pathname?.startsWith('/human-service')) {
      router.push('/dashboard');
    }
  }, [isLoading, isAuthenticated, user, pathname, router]);

  return <>{children}</>;
}
