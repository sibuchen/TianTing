import AdminLayout from '@/components/layout/AdminLayout';
import React from 'react';

export default function AdminRouteLayout({ children }: { children: React.ReactNode }) {
  return <AdminLayout>{children}</AdminLayout>;
}
