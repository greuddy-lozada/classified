import { defineStore } from 'pinia';
import { api } from 'src/boot/axios';

export interface Membresia {
  organizacion_id: string;
  organizacion_nombre: string;
  rol: string;
}

export interface Me {
  id: string;
  email: string;
  es_plataforma: boolean;
  organizacion_id: string | null;
  rol: string | null;
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    me: null as Me | null,
    membresias: [] as Membresia[],
  }),
  getters: {
    isAuthenticated: (s) => s.me !== null,
  },
  actions: {
    persist(access: string, refresh: string) {
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
    },
    async login(email: string, password: string) {
      const { data } = await api.post('/auth/login', { email, password });
      this.persist(data.access_token, data.refresh_token);
      this.membresias = data.membresias;
      const { data: me } = await api.get('/auth/me');
      this.me = me;
      return data;
    },
    async seleccionar(organizacion_id: string, rol: string) {
      const { data } = await api.post('/auth/seleccionar', { organizacion_id, rol });
      this.persist(data.access_token, data.refresh_token);
      const { data: me } = await api.get('/auth/me');
      this.me = me;
    },
    async hydrate() {
      if (!localStorage.getItem('access_token')) return;
      const { data } = await api.get('/auth/me');
      this.me = data;
    },
    logout() {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      this.me = null;
      this.membresias = [];
    },
  },
});
