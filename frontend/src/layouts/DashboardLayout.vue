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
        return [
          { title: 'Mis pupilos', caption: 'Fichas', icon: 'family_restroom', link: '/dashboard' },
          { title: 'Inscripción', caption: 'Estado y recaudos', icon: 'assignment', link: '/dashboard/mis-inscripciones' },
          { title: 'Boletín', caption: 'Notas e informe', icon: 'menu_book', link: '/dashboard/mis-inscripciones' },
          { title: 'Asistencia', caption: 'Faltas', icon: 'event_available', link: '/dashboard/mis-faltas' },
        ];
      }
      return [
        { title: 'Inicio', caption: 'Plantel', icon: 'school', link: '/dashboard' },
        { title: 'Año escolar', caption: 'Lapsos, grados, secciones', icon: 'event', link: '/dashboard/periodo' },
        { title: 'Inscripciones', caption: 'Cupo y sección', icon: 'how_to_reg', link: '/dashboard/inscripciones' },
        { title: 'Evaluación', caption: 'Notas e informes', icon: 'grade', link: '/dashboard/evaluacion' },
        { title: 'Asistencia', caption: 'Lista del día', icon: 'event_available', link: '/dashboard/asistencia' },
      ];
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
