import { useAuthStore } from 'src/stores/auth';

export function useAuth() {
  return useAuthStore();
}
