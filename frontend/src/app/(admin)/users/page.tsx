'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { App, Modal, Form, Input, Select, Popconfirm } from 'antd';
import { usersApi } from '@/lib/api';

interface User {
  id: string;
  avatar: string | null;
  username: string;
  email: string;
  role: string;
  status: 'active' | 'disabled';
  createdAt: string;
}

export default function UsersPage() {
  const { message } = App.useApp();
  const t = useTranslations('Users');
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [editUser, setEditUser] = useState<User | null>(null);
  const [form] = Form.useForm();
  const [saving, setSaving] = useState(false);

  const fetchUsers = useCallback(() => {
    setLoading(true);
    usersApi.list()
      .then((res: any) => {
        const items = Array.isArray(res?.data) ? res.data : res?.data?.items ?? [];
        setUsers(items);
      })
      .catch(() => {
        setUsers([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleCreate = () => {
    setEditUser(null);
    form.resetFields();
    setCreateOpen(true);
  };

  const handleEdit = (user: User) => {
    setEditUser(user);
    form.setFieldsValue({
      username: user.username,
      email: user.email,
      role: user.role,
    });
    setCreateOpen(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      if (editUser) {
        await usersApi.update(editUser.id, values);
        message.success(t('updateSuccess') || 'User updated');
      } else {
        await usersApi.create(values);
        message.success(t('createSuccess') || 'User created');
      }
      setCreateOpen(false);
      fetchUsers();
    } catch (error: any) {
      if (error?.errorFields) return;
      const detail = error?.response?.data?.detail;
      if (detail) {
        const messages = Array.isArray(detail)
          ? detail.map((d: any) => d.msg).join('; ')
          : String(detail);
        message.error(messages || t('saveFailed'));
      } else {
        message.error(t('saveFailed') || 'Save failed');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (userId: string) => {
    try {
      await usersApi.delete(userId);
      message.success(t('deleteSuccess') || 'User deleted');
      fetchUsers();
    } catch {
      message.error(t('deleteFailed') || 'Delete failed');
    }
  };

  const roleOptions = editUser
    ? (editUser.role === 'admin'
        ? [{ value: 'admin', label: t('admin') }]
        : [{ value: 'admin', label: t('admin') }, { value: 'operator', label: t('operator') }])
    : [{ value: 'admin', label: t('admin') }, { value: 'operator', label: t('operator') }];

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="bg-card-bg rounded-xl shadow-soft overflow-hidden border border-outline-variant">
        <div className="p-6 flex items-center justify-between border-b border-outline-variant bg-surface-container-low/30">
          <div>
            <h2 className="text-2xl font-semibold text-on-surface">{t('title')}</h2>
            <p className="text-sm text-on-surface-variant mt-1">{t('subtitle')}</p>
          </div>
          <button
            onClick={handleCreate}
            className="bg-primary text-on-primary px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 hover:bg-primary-container hover:scale-[1.02] transition-all shadow-sm"
          >
            <span className="material-symbols-outlined text-[20px]">add</span>
            {t('createUser')}
          </button>
        </div>

        <div className="overflow-x-auto">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <span className="material-symbols-outlined animate-spin text-primary text-3xl">progress_activity</span>
            </div>
          ) : (
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-container-low text-xs font-medium text-on-surface-variant">
                <th className="py-4 px-6 font-medium whitespace-nowrap">{t('avatar')}</th>
                <th className="py-4 px-6 font-medium whitespace-nowrap">{t('username')}</th>
                <th className="py-4 px-6 font-medium whitespace-nowrap">{t('email')}</th>
                <th className="py-4 px-6 font-medium whitespace-nowrap">{t('role')}</th>
                <th className="py-4 px-6 font-medium whitespace-nowrap">{t('status')}</th>
                <th className="py-4 px-6 font-medium whitespace-nowrap">{t('createdAt')}</th>
                <th className="py-4 px-6 font-medium whitespace-nowrap text-right">{t('actions')}</th>
              </tr>
            </thead>
            <tbody className="font-body-md text-on-surface divide-y divide-outline-variant">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-surface-container-lowest hover:-translate-y-[1px] transition-all group">
                  <td className="py-3 px-6">
                    {user.avatar ? (
                      <img
                        src={user.avatar}
                        alt="Avatar"
                        className="w-10 h-10 rounded-full object-cover shadow-sm border border-outline-variant"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-surface-container-high flex items-center justify-center text-on-surface-variant font-medium">
                        {user.username.substring(0, 2).toUpperCase()}
                      </div>
                    )}
                  </td>
                  <td className="py-3 px-6 font-medium">{user.username}</td>
                  <td className="py-3 px-6 text-on-surface-variant">{user.email}</td>
                  <td className="py-3 px-6">
                    <span className="inline-flex items-center px-2 py-1 rounded-md bg-surface-container text-on-surface-variant font-label-sm">
                      {user.role}
                    </span>
                  </td>
                  <td className="py-3 px-6">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full font-label-sm gap-1 ${user.status === 'active'
                        ? 'bg-success/10 text-success'
                        : 'bg-error/10 text-error'
                       }`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${user.status === 'active' ? 'bg-success' : 'bg-error'
                        }`}></span>
                      {user.status === 'active' ? t('active') : t('disabled')}
                    </span>
                  </td>
                  <td className="py-3 px-6 text-on-surface-variant">{user.createdAt}</td>
                  <td className="py-3 px-6 text-right">
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => handleEdit(user)}
                        className="p-2 text-on-surface-variant hover:text-primary hover:bg-primary-container/30 rounded-lg transition-all duration-200 flex items-center justify-center"
                        title={t('edit') || 'Edit'}
                      >
                        <span className="material-symbols-outlined text-[20px]">edit</span>
                      </button>
                      <Popconfirm
                        title={t('confirmDelete') || 'Delete this user?'}
                        onConfirm={() => handleDelete(user.id)}
                        okText={t('yes') || 'Yes'}
                        cancelText={t('no') || 'No'}
                      >
                        <button
                          className="p-2 text-on-surface-variant hover:text-error hover:bg-error/10 rounded-lg transition-all duration-200 flex items-center justify-center"
                          title={t('delete') || 'Delete'}
                        >
                          <span className="material-symbols-outlined text-[20px]">delete</span>
                        </button>
                      </Popconfirm>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          )}
        </div>

        <div className="bg-card-bg p-4 flex items-center justify-between">
          <span className="font-body-sm text-on-surface-variant">{t('showing', { start: 1, end: users.length, total: users.length })}</span>
          <div className="flex gap-1">
            <button className="px-3 py-1 rounded border border-outline-variant text-on-surface-variant hover:bg-surface-container-high disabled:opacity-50 font-label-md transition-colors" disabled>
              {t('prev')}
            </button>
            <button className="px-3 py-1 rounded bg-primary text-on-primary font-label-md shadow-sm">1</button>
            <button className="px-3 py-1 rounded border border-outline-variant text-on-surface-variant hover:bg-surface-container-high disabled:opacity-50 font-label-md transition-colors" disabled>
              {t('next')}
            </button>
          </div>
        </div>
      </div>

      <Modal
        title={<span className="text-lg font-bold text-on-surface">{editUser ? t('editUser') || 'Edit User' : t('createUser')}</span>}
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={handleSave}
        confirmLoading={saving}
        okText={t('save') || 'Save'}
        cancelText={t('cancel') || 'Cancel'}
        centered
        width={480}
      >
        <Form form={form} layout="vertical" className="mt-4">
          <Form.Item
            name="username"
            label={t('username') || 'Username'}
            rules={[
              { required: true, message: t('usernameRequired') || 'Username is required' },
              { min: 3, message: '用户名至少3个字符' },
              { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线' },
            ]}
          >
            <Input className="rounded-lg" />
          </Form.Item>
          <Form.Item
            name="email"
            label={t('email') || 'Email'}
            rules={[
              { required: true, message: t('emailRequired') || 'Email is required' },
              { type: 'email', message: t('emailInvalid') || 'Invalid email' },
            ]}
          >
            <Input className="rounded-lg" />
          </Form.Item>
          {!editUser && (
            <Form.Item
              name="password"
              label={t('password') || 'Password'}
              rules={[
                { required: true, message: t('passwordRequired') || 'Password is required' },
                { min: 8, message: '密码至少8个字符' },
              ]}
            >
              <Input.Password className="rounded-lg" />
            </Form.Item>
          )}
          <Form.Item name="role" label={t('role') || 'Role'}>
            <Select className="rounded-lg" options={roleOptions} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
