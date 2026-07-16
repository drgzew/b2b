import { apiClient } from './client';
import type { Author } from './types';

export const authorsAPI = {
  getAuthor: (authorId: number) => apiClient.get<Author>(`/authors/${authorId}`),
};