<template>
  <q-layout view="lHh Lpr lFf" class="app-shell">
    <q-header class="app-header">
      <q-toolbar>
        <q-btn flat dense round icon="menu" aria-label="Abrir menú" @click="toggleLeftDrawer" />
        <q-toolbar-title class="text-weight-bold">Classified</q-toolbar-title>
        <div class="app-header__meta ellipsis">
          <div class="text-caption">{{ plantel }}</div>
          <div class="text-caption text-grey-4">{{ rolLabel }}</div>
        </div>
        <q-btn flat no-caps label="Salir" @click="logout" />
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" show-if-above bordered class="app-drawer">
      <div class="app-drawer__brand">
        <div class="text-weight-bold">Classified</div>
        <div class="text-caption">{{ plantel }}</div>
      </div>
      <q-list>
        <DashLink v-for="link in linksList" :key="link.title" v-bind="link" />
      </q-list>
    </q-drawer>

    <q-page-container class="app-main">
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script lang="ts">
import { computed, defineComponent, onMounted, onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import DashLink, { type DashLinkProps } from '../modules/dashboard/DashLink.vue';
import { useAuthStore } from 'src/stores/auth';

const ROLES: Record<string, string> = {
  direccion: 'Dirección',
  secretaria: 'Secretaría',
  docente: 'Docente',
  representante: 'Representante',
};

export default defineComponent({
  name: 'DashboardLayout',
  components: { DashLink },
  setup() {
    const leftDrawerOpen = ref(false);
    const auth = useAuthStore();
    const router = useRouter();
    const plantel = computed(() => {
      const org = auth.membresias.find((m) => m.organizacion_id === auth.me?.organizacion_id);
      return org?.organizacion_nombre ?? (auth.me?.es_plataforma ? 'Plataforma' : 'Plantel');
    });
    const rolLabel = computed(() => {
      if (auth.me?.es_plataforma && !auth.me.rol) return 'Plataforma';
      return ROLES[auth.me?.rol ?? ''] ?? auth.me?.rol ?? '';
    });
    const linksList = computed<DashLinkProps[]>(() => {
      if (auth.me?.es_plataforma && !auth.me.rol) {
        return [{ title: 'Planteles', caption: 'Alta de colegios', icon: 'apartment', link: '/plataforma' }];
      }
      if (auth.me?.rol === 'representante') {
        return [
          { title: 'Mis pupilos', caption: 'Inicio', icon: 'family_restroom', link: '/dashboard', exact: true },
          { title: 'Inscripción', caption: 'Estado y recaudos', icon: 'assignment', link: '/dashboard/mis-inscripciones' },
          { title: 'Asistencia', caption: 'Faltas', icon: 'event_available', link: '/dashboard/mis-faltas' },
          { title: 'Cobro', caption: 'Matrícula y mensualidad', icon: 'payments', link: '/dashboard/mis-cobros' },
        ];
      }
      if (auth.me?.rol === 'docente') {
        return [
          { title: 'Inicio', caption: 'Plantel', icon: 'school', link: '/dashboard', exact: true },
          { title: 'Evaluación', caption: 'Notas e informes', icon: 'grade', link: '/dashboard/evaluacion' },
          { title: 'Asistencia', caption: 'Lista del día', icon: 'event_available', link: '/dashboard/asistencia' },
        ];
      }
      return [
        { title: 'Inicio', caption: 'Plantel', icon: 'school', link: '/dashboard', exact: true },
        { title: 'Fichas', caption: 'Alumnos y representantes', icon: 'badge', link: '/dashboard/fichas' },
        { title: 'Año escolar', caption: 'Lapsos, grados, secciones', icon: 'event', link: '/dashboard/periodo' },
        { title: 'Inscripciones', caption: 'Cupo y sección', icon: 'how_to_reg', link: '/dashboard/inscripciones' },
        { title: 'Evaluación', caption: 'Notas e informes', icon: 'grade', link: '/dashboard/evaluacion' },
        { title: 'Asistencia', caption: 'Lista del día', icon: 'event_available', link: '/dashboard/asistencia' },
        { title: 'Cobro', caption: 'Matrícula y mensualidad', icon: 'payments', link: '/dashboard/cobro' },
      ];
    });

    onMounted(() => document.body.classList.add('body--dashboard'));
    onUnmounted(() => document.body.classList.remove('body--dashboard'));

    return {
      plantel,
      rolLabel,
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

<style scoped>
.app-header {
  background: #333243;
  color: #f4f1ea;
  box-shadow: none;
}

.app-header__meta {
  max-width: 14rem;
  text-align: right;
  margin-right: 0.75rem;
}

.app-drawer {
  background: #2a2838;
  color: #f4f1ea;
}

.app-drawer__brand {
  padding: 1.25rem 1.15rem 0.75rem;
}

.app-main {
  background: #f4f1ea;
  min-height: 100vh;
}
</style>
