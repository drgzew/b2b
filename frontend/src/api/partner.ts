import { apiClient } from './client';
import type { DigestEntry, Favorite, Internship, Request, Subscription } from './types';

export interface Partner {
  id: number;
  name: string;
  contact_email: string;
}

export interface SubscriptionWithDescription extends Subscription {
  description?: string;
}

export const partnerAPI = {
  getMe: () => apiClient.get<Partner>('/partner/me'),

  getSubscriptions: () => apiClient.get<SubscriptionWithDescription[]>('/partner/subscriptions'),

  replaceSubscriptions: (data: { subscriptions: { name: string; tags: string[]; description?: string }[] }) =>
    apiClient.put<SubscriptionWithDescription[]>('/partner/subscriptions', data),

  getDigest: (subscriptionId: number) =>
    apiClient.get<DigestEntry[]>(`/partner/subscriptions/${subscriptionId}/digest`),

  getReadAccess: (artifactId: number) =>
    apiClient.get<{ mode: 'redirect' | 'pdf'; url?: string | null }>(`/partner/artifacts/${artifactId}/read`),

  createRequest: (data: { artifact_id: number; type: 'full_text' | 'internship' | 'rnd' }) =>
    apiClient.post<Request>('/partner/requests', data),

  getFavorites: () => apiClient.get<Favorite[]>('/partner/favorites'),
  addFavorite: (artifactId: number) => apiClient.post<Favorite>('/partner/favorites', { artifact_id: artifactId }),
  removeFavorite: (favoriteId: number) => apiClient.delete(`/partner/favorites/${favoriteId}`),

  getInternships: () => apiClient.get<Internship[]>('/partner/internships'),
  createInternship: (artifactId: number, studentName: string) =>
    apiClient.post<Internship>('/partner/internships', { artifact_id: artifactId, student_name: studentName }),
  updateInternshipStatus: (internshipId: number, status: string) =>
    apiClient.patch<Internship>(`/partner/internships/${internshipId}/status`, { status }),
};