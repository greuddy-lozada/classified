<template>
  <AppPage title="Año escolar" subtitle="Tres lapsos por año. Cierra un lapso cuando termine la carga.">
    <div class="app-card">
      <h2 class="app-card__title">Nuevo año</h2>
      <q-form class="row q-col-gutter-md" @submit.prevent="crearAnio">
        <div class="col-12 col-sm-8">
          <q-input v-model="nuevoAnio" outlined label="Nombre (ej. 2026-2027)" />
        </div>
        <div class="col-12 col-sm-4">
          <q-btn unelevated type="submit" color="primary" text-color="dark" no-caps label="Crear año" class="full-width" />
        </div>
      </q-form>
    </div>

    <p v-if="!anios.length" class="app-empty">Crea el año escolar para empezar.</p>
    <div v-for="anio in anios" :key="anio.id" class="app-card">
      <div class="row items-center q-mb-md">
        <div class="text-subtitle1 text-weight-bold col">{{ anio.nombre }}</div>
        <q-badge v-if="anio.activo" color="primary" text-color="dark" label="activo" />
      </div>
      <div class="row q-col-gutter-sm q-mb-md">
        <div v-for="l in anio.lapsos" :key="l.id" class="col-12 col-sm-4">
          <q-btn
            unelevated
            no-caps
            class="full-width"
            :color="l.cerrado ? 'grey-5' : 'primary'"
            :text-color="l.cerrado ? 'dark' : 'dark'"
            :label="l.cerrado ? `${l.nombre}: reabrir` : `${l.nombre}: cerrar`"
            @click="l.cerrado ? reabrirLapso(l.id) : cerrarLapso(l.id)"
          />
        </div>
      </div>
      <q-form class="row q-col-gutter-md q-mb-md" @submit.prevent="crearGrado(anio.id)">
        <div class="col-12 col-sm-6 col-md-3">
          <q-select v-model="formGrado.nivel" outlined emit-value map-options :options="niveles" label="Nivel" />
        </div>
        <div class="col-12 col-sm-6 col-md-4">
          <q-input v-model="formGrado.nombre" outlined label="Grado (4°, 3er año)" />
        </div>
        <div class="col-12 col-sm-6 col-md-3">
          <q-select v-model="formGrado.esquema" outlined emit-value map-options :options="esquemas" label="Esquema" clearable />
        </div>
        <div class="col-12 col-sm-6 col-md-2">
          <q-btn unelevated type="submit" color="primary" text-color="dark" no-caps label="Grado" class="full-width" />
        </div>
      </q-form>
      <p v-if="!(gradosPorAnio[anio.id] ?? []).length" class="app-empty">Sin grados en este año.</p>
      <q-list v-else separator>
        <q-item v-for="g in gradosPorAnio[anio.id] ?? []" :key="g.id">
          <q-item-section>
            <q-item-label>{{ etiquetaNivel(g.nivel) }} · {{ g.nombre }}</q-item-label>
            <q-item-label caption>
              {{ g.esquema_evaluacion === 'informe' ? 'Informe' : 'Numérico' }} ·
              {{ g.secciones.map((s) => `${s.letra} ${s.turno === 'tarde' ? 'tarde' : 'mañana'}`).join(', ') || 'sin sección' }}
            </q-item-label>
          </q-item-section>
          <q-item-section side>
            <q-btn flat no-caps color="primary" label="Sección A mañana" @click="crearSeccion(g.id, 'A', 'manana')" />
          </q-item-section>
        </q-item>
      </q-list>
    </div>
  </AppPage>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import { useQuasar } from 'quasar';
import { api } from 'src/boot/axios';
import AppPage from '../dashboard/AppPage.vue';

interface Lapso {
  id: string;
  numero: number;
  nombre: string;
  cerrado: boolean;
}
interface Seccion {
  id: string;
  letra: string;
  turno: string;
}
interface Grado {
  id: string;
  nivel: string;
  nombre: string;
  esquema_evaluacion: string;
  secciones: Seccion[];
}
interface Anio {
  id: string;
  nombre: string;
  activo: boolean;
  lapsos: Lapso[];
}

const $q = useQuasar();
const anios = ref<Anio[]>([]);
const gradosPorAnio = ref<Record<string, Grado[]>>({});
const nuevoAnio = ref('2026-2027');
const niveles = [
  { label: 'Inicial', value: 'inicial' },
  { label: 'Primaria', value: 'primaria' },
  { label: 'Media', value: 'media' },
];
const esquemas = [
  { label: 'Informe', value: 'informe' },
  { label: 'Numérico', value: 'numerico' },
];

function etiquetaNivel(v: string) {
  const map: Record<string, string> = { inicial: 'Inicial', primaria: 'Primaria', media: 'Media' };
  return map[v] ?? v;
}
const formGrado = reactive({ nivel: 'primaria', nombre: '', esquema: null as string | null });

async function cargar() {
  const { data } = await api.get<Anio[]>('/periodo/anios');
  anios.value = data;
  for (const anio of data) {
    const res = await api.get<Grado[]>('/periodo/grados', { params: { anio_escolar_id: anio.id } });
    gradosPorAnio.value[anio.id] = res.data;
  }
}

async function crearAnio() {
  try {
    await api.post('/periodo/anios', { nombre: nuevoAnio.value });
    await cargar();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo crear el año' });
  }
}

async function crearGrado(anioId: string) {
  try {
    const payload: Record<string, unknown> = {
      anio_escolar_id: anioId,
      nivel: formGrado.nivel,
      nombre: formGrado.nombre,
    };
    if (formGrado.esquema) payload.esquema_evaluacion = formGrado.esquema;
    await api.post('/periodo/grados', payload);
    formGrado.nombre = '';
    await cargar();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo crear el grado' });
  }
}

async function crearSeccion(gradoId: string, letra: string, turno: string) {
  try {
    await api.post('/periodo/secciones', { grado_id: gradoId, letra, turno });
    await cargar();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo crear la sección' });
  }
}

async function cerrarLapso(id: string) {
  try {
    await api.post(`/periodo/lapsos/${id}/cerrar`);
    await cargar();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo cerrar el lapso' });
  }
}

async function reabrirLapso(id: string) {
  try {
    await api.post(`/periodo/lapsos/${id}/reabrir`);
    await cargar();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo reabrir el lapso' });
  }
}

onMounted(cargar);
</script>
