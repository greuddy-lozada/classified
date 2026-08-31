<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn flat dense round icon="menu" aria-label="Menu" @click="toggleLeftDrawer" />

        <q-toolbar-title> Classified </q-toolbar-title>

        <q-btn flat label="Salir" @click="logout" />
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" show-if-above bordered>
      <q-list>
        <q-item-label header> Logo </q-item-label>

        <DashLink v-for="link in linksList" :key="link.title" v-bind="link" />
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script lang="ts">
import { computed, defineComponent, ref } from 'vue';
import { useRouter } from 'vue-router';
import DashLink, { type DashLinkProps } from '../modules/dashboard/DashLink.vue';
import { useAuthStore } from 'src/stores/auth';

export default defineComponent({
  name: 'DashboardLayout',
  components: { DashLink },
  setup() {
    const leftDrawerOpen = ref(false);
    const auth = useAuthStore();
    const router = useRouter();
    const linksList = computed<DashLinkProps[]>(() => {
      if (auth.me?.es_plataforma && !auth.me.rol) {
        return [{ title: 'Planteles', caption: 'Alta de colegios', icon: 'apartment', link: '/plataforma' }];
      }
      if (auth.me?.rol === 'representante') {
        return [{ title: 'Mis pupilos', caption: 'Fichas', icon: 'family_restroom', link: '/dashboard' }];
      }
      return [{ title: 'Inicio', caption: 'Plantel', icon: 'school', link: '/dashboard' }];
    });
    return {
      linksList,
      leftDrawerOpen,
      toggleLeftDrawer() {
        leftDrawerOpen.value = !leftDrawerOpen.value;
      },
      logout() {
        auth.logout();
        void router.push('/login');
      },
    };
  },
});
</script>
