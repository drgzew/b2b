import { apiClient } from './client';
import type { Artifact, Author, AuthorRequest, Internship } from './types';

export const authorAPI = {
  getMe: () => apiClient.get<Author>('/author/me'),

  updateJobStatus: (jobStatus: string) =>
    apiClient.patch<Author>('/author/me/job-status', { job_status: jobStatus }),

  getArtifacts: () => apiClient.get<Artifact[]>('/author/artifacts'),

  updateReadPolicy: (artifactId: number, readPolicy: 'open' | 'requires_approval') =>
    apiClient.patch<Artifact>(`/author/artifacts/${artifactId}/read-policy`, {
      read_policy: readPolicy,
    }),

  getRequests: () => apiClient.get<AuthorRequest[]>('/author/requests'),

  decideOnRequest: (requestId: number, approve: boolean) =>
    apiClient.post<AuthorRequest>(`/author/requests/${requestId}/decision`, { approve }),

  getInternships: () => apiClient.get<Internship[]>('/author/internships'),

  respondToInternship: (internshipId: number, accept: boolean) =>
    apiClient.post(`/author/internships/${internshipId}/respond`, { accept }),
};