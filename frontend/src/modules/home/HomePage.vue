<template>
  <AppPage :title="greeting" :subtitle="subtitulo">
    <div v-if="pupilos.length" class="app-card">
      <h2 class="app-card__title">Pupilos</h2>
      <q-list separator>
        <q-item v-for="p in pupilos" :key="p.id">
          <q-item-section>
            <q-item-label>{{ p.alumno_nombres }} {{ p.alumno_apellidos }}</q-item-label>
            <q-item-label caption>{{ estadoIns(p.estado) }} · matrícula {{ estadoPago(p.estado_matricula) }}</q-item-label>
          </q-item-section>
          <q-item-section side>
            <q-btn unelevated color="primary" no-caps label="Boletín" :to="`/dashboard/boletines/${p.id}`" />
          </q-item-section>
        </q-item>
      </q-list>
    </div>
    <div v-else-if="auth.me?.rol === 'representante'" class="app-card">
      <p class="app-empty">Aún no hay pupilos vinculados a tu usuario.</p>
    </div>
    <div v-else class="row q-col-gutter-md">
      <div v-for="card in atajos" :key="card.link" class="col-12 col-sm-6">
        <q-item clickable :to="card.link" class="app-card q-mb-none">
          <q-item-section avatar>
            <q-icon :name="card.icon" color="primary" size="28px" />
          </q-item-section>
          <q-item-section>
            <q-item-label class="text-weight-bold">{{ card.title }}</q-item-label>
            <q-item-label caption>{{ card.caption }}</q-item-label>
          </q-item-section>
        </q-item>
      </div>
    </div>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useAuthStore } from 'src/stores/auth';
import { api } from 'src/boot/axios';
import AppPage from '../dashboard/AppPage.vue';

interface Pupilo {
  id: string;
  alumno_nombres: string;
  alumno_apellidos: string;
  estado: string;
  estado_matricula: string;
}

const auth = useAuthStore();
const pupilos = ref<Pupilo[]>([]);
const greeting = computed(() => {
  if (auth.me?.es_plataforma && !auth.me.rol) return 'Plataforma';
  if (auth.me?.rol === 'representante') return 'Tus pupilos';
  return 'Plantel';
});
const subtitulo = computed(() => {
  if (auth.me?.rol === 'representante') return 'Consulta boletín, faltas y cobro de tus alumnos.';
  if (auth.me?.rol === 'docente') return 'Pasa lista y carga notas de tus secciones.';
  return 'Fichas, cupo, asistencia, notas y cobro en un solo lugar.';
});
const atajos = computed(() => {
  if (auth.me?.rol === 'docente') {
    return [
      { title: 'Evaluación', caption: 'Notas e informes', icon: 'grade', link: '/dashboard/evaluacion' },
      { title: 'Asistencia', caption: 'Lista del día', icon: 'event_available', link: '/dashboard/asistencia' },
    ];
  }
  return [
    { title: 'Fichas', caption: 'Alumnos y representantes', icon: 'badge', link: '/dashboard/fichas' },
    { title: 'Año escolar', caption: 'Lapsos, grados y secciones', icon: 'event', link: '/dashboard/periodo' },
    { title: 'Inscripciones', caption: 'Cupo y sección', icon: 'how_to_reg', link: '/dashboard/inscripciones' },
    { title: 'Asistencia', caption: 'Lista del día', icon: 'event_available', link: '/dashboard/asistencia' },
  ];
});

function estadoIns(v: string) {
  const map: Record<string, string> = {
    preinscrito: 'Preinscrito',
    inscrito: 'Inscrito',
    activo: 'Activo',
    retirado: 'Retirado',
  };
  return map[v] ?? v;
}

function estadoPago(v: string) {
  const map: Record<string, string> = { pendiente: 'pendiente', pagada: 'pagada', morosa: 'morosa' };
  return map[v] ?? v;
}

onMounted(async () => {
  if (auth.me?.rol !== 'representante') return;
  const { data } = await api.get<Pupilo[]>('/inscripciones/mias');
  pupilos.value = data;
});
</script>
