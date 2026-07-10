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
};