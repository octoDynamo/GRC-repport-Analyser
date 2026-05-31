import axios from 'axios';
import { useAuthStore } from '../store/authStore';
import type { AdminUser, AdminStats, ReferentielConfig, ApiResponse } from '../types';

export const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
});

// Request interceptor to attach JWT token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Optional: Response interceptor for handling 401s (logout on expiration)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
    }
    return Promise.reject(error);
  }
);

// ── Admin API ──────────────────────────────────────────────────────────────────

export const adminApi = {
  getStats: () =>
    api.get<ApiResponse<AdminStats>>('/admin/stats').then((r) => r.data.data),

  getUsers: () =>
    api.get<ApiResponse<AdminUser[]>>('/admin/users').then((r) => r.data.data),

  createUser: (body: { nom: string; email: string; password: string; role: string }) =>
    api.post<ApiResponse<AdminUser>>('/admin/users', body).then((r) => r.data.data),

  updateUser: (id: string, body: { nom?: string; role?: string }) =>
    api.patch<ApiResponse<AdminUser>>(`/admin/users/${id}`, body).then((r) => r.data.data),

  deleteUser: (id: string) =>
    api.delete(`/admin/users/${id}`).then((r) => r.data),

  getReferentiels: () =>
    api.get<ApiResponse<ReferentielConfig[]>>('/admin/referentiels').then((r) => r.data.data),

  updateReferentiel: (
    ref: string,
    body: { actif?: boolean; seuil_conformite?: number; description?: string }
  ) =>
    api
      .patch<ApiResponse<ReferentielConfig>>(`/admin/referentiels/${ref}`, body)
      .then((r) => r.data.data),
};
