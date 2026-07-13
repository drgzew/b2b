import { apiClient } from './client';

export interface Partner {
  id: number;
  name: string;
  contact_email: string;
}

export interface Subscription {
  id: number;
  name: string;
  tags: string[];
  description?: string;
}

export interface Artifact {
  id: number;
  title: string;
  type: 'vkr' | 'article' | 'talk' | 'event';
  annotation: string;
  file_path: string | null;
  curator_status: 'draft' | 'approved' | 'rejected';
  access_level: 'full' | 'annotation_only' | 'none';
  author_name: string;
  created_at: string;
  tags: { id: number; name: string }[];
}

export interface DigestEntry {
  artifact: Artifact;
  relevance: number;
}

export interface InternshipRequest {
  id: number;
  artifact_id: number;
  artifact: Artifact;
  status: 'sent' | 'accepted' | 'in_progress' | 'rejected' | 'completed';
  created_at: string;
  student_name?: string;
  response_date?: string;
}

export interface FavoriteArtifact {
  id: number;
  artifact_id: number;
  artifact: Artifact;
  added_at: string;
}

export const partnerAPI = {
  getMe: () => apiClient.get<Partner>('/partner/me'),
  // GET /partner/subscriptions
  getSubscriptions: () => apiClient.get<Subscription[]>('/partner/subscriptions'),

  // GET /partner/subscriptions/{id}/digest
  getDigest: (subscriptionId: number) =>
    apiClient.get<DigestEntry[]>(`/partner/subscriptions/${subscriptionId}/digest`),

  // POST /partner/requests
  createRequest: (data: { artifact_id: number; type: 'full_text' | 'internship' | 'rnd' }) =>
    apiClient.post('/partner/requests', data),

  // PUT /partner/subscriptions — заменить весь набор подписок партнёра
  replaceSubscriptions: (data: { subscriptions: { name: string; tags: string[] }[] }) =>
    apiClient.put<Subscription[]>('/partner/subscriptions', data),

  // GET /partner/internships — получить все приглашения на стажировку
  getInternships: () => apiClient.get<InternshipRequest[]>('/partner/internships'),

  // PATCH /partner/internships/{id}/status — обновить статус стажировки
  updateInternshipStatus: (internshipId: number, status: string) =>
    apiClient.patch<InternshipRequest>(`/partner/internships/${internshipId}/status`, { status }),

  // GET /partner/favorites — получить все избранные артефакты
  getFavorites: () => apiClient.get<FavoriteArtifact[]>('/partner/favorites'),

  // POST /partner/favorites — добавить артефакт в избранное
  addFavorite: (artifactId: number) =>
    apiClient.post('/partner/favorites', {
      artifact_id: artifactId
    }),

  // DELETE /partner/favorites/{id} — удалить из избранного
  removeFavorite: (favoriteId: number) =>
    apiClient.delete(`/partner/favorites/${favoriteId}`),


};