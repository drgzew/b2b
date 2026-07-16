import { apiClient } from './client';
import type { Teacher } from './types';

export const teachersAPI = {
  getTeacher: (teacherId: number) => apiClient.get<Teacher>(`/teachers/${teacherId}`),
};