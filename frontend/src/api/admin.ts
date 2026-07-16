import { apiClient } from './client';

export interface AdminUser {
  id: number;
  email: string;
  role: 'partner' | 'curator' | 'admin' | 'author';
  partner_id?: number | null;
  author_id?: number | null;
}

export interface AdminUserCreate {
  email: string;
  password: string;
  role: 'partner' | 'curator' | 'admin' | 'author';
  partner_id?: number | null;
  author_id?: number | null;
}

export interface AdminPartner {
  id: number;
  name: string;
  contact_email: string;
}

export interface AdminPartnerCreate {
  name: string;
  contact_email: string;
}

// Минимум полей — используется только для резолва author_id -> ФИО
// на странице «Пользователи», не полный профиль (см. AuthorProfile.tsx).
export interface AdminAuthor {
  id: number;
  full_name: string;
}

export interface ImportResult {
  total: number;
  imported: number;
  skipped: number;
  errors: number;
  error_details: string[];
  tags_created: number;
  tags_existing: number;
  with_annotation: number;
  with_tags: number;
}

export const adminAPI = {
  // GET/POST /admin/users
  getUsers: () => apiClient.get<AdminUser[]>('/admin/users'),
  createUser: (data: AdminUserCreate) => apiClient.post<AdminUser>('/admin/users', data),

  // GET/POST /admin/partners
  getPartners: () => apiClient.get<AdminPartner[]>('/admin/partners'),
  createPartner: (data: AdminPartnerCreate) => apiClient.post<AdminPartner>('/admin/partners', data),

  // GET /authors — общий список авторов (не под /admin, но доступен роли admin
  // на бэке), нужен только для резолва author_id -> ФИО в таблице пользователей.
  getAuthors: () => apiClient.get<AdminAuthor[]>('/authors'),

  // POST /admin/import — normalized.json из парсера, multipart-загрузка файла.
  // Content-Type для multipart axios выставляет сам (с нужным boundary), если
  // не переопределять его вручную — здесь специально не трогаем заголовки.
  importArtifacts: (file: File, wipe: boolean) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post<ImportResult>('/admin/import', formData, {
      params: { wipe },
    });
  },
};
