<template>
  <AppPage title="Año escolar" subtitle="Tres lapsos por año. Cierra un lapso cuando termine la carga.">
    <div class="app-card">
      <h2 class="app-card__title">Nuevo año</h2>
      <q-form class="row q-col-gutter-md" @submit.prevent="crearAnio">
        <div class="col-12 col-sm-8">
          <q-input v-model="nuevoAnio" outlined label="Nombre (ej. 2026-2027)" />
        </div>
        <div class="col-12 col-sm-4">
          <q-btn unelevated type="submit" color="primary" no-caps label="Crear año" class="full-width" />
        </div>
      </q-form>
    </div>

    <p v-if="!anios.length" class="app-empty">Crea el año escolar para empezar.</p>
    <div v-for="anio in anios" :key="anio.id" class="app-card">
      <div class="row items-center q-mb-md">
        <div class="text-subtitle1 text-weight-bold col">{{ anio.nombre }}</div>
        <q-badge v-if="anio.activo" color="primary" label="activo" class="q-mr-sm" />
        <q-btn flat no-caps color="primary" label="Renombrar" @click="renombrarAnio(anio)" />
        <q-btn flat no-caps color="negative" label="Borrar" @click="borrarAnio(anio)" />
      </div>
      <div class="row q-col-gutter-sm q-mb-md">
        <div v-for="l in anio.lapsos" :key="l.id" class="col-12 col-sm-4">
          <q-btn
            unelevated
            no-caps
            class="full-width"
            :color="l.cerrado ? 'grey-5' : 'primary'"
            :text-color="l.cerrado ? 'dark' : 'white'"
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
          <q-btn unelevated type="submit" color="primary" no-caps label="Grado" class="full-width" />
        </div>
      </q-form>
      <p v-if="!(gradosPorAnio[anio.id] ?? []).length" class="app-empty">Sin grados en este año.</p>
      <q-list v-else separator>
        <template v-for="g in gradosPorAnio[anio.id] ?? []" :key="g.id">
          <q-item>
            <q-item-section>
              <q-item-label>{{ etiquetaNivel(g.nivel) }} · {{ g.nombre }}</q-item-label>
              <q-item-label caption>{{ g.esquema_evaluacion === 'informe' ? 'Informe' : 'Numérico' }}</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-btn flat no-caps color="primary" label="Renombrar" @click="renombrarGrado(g)" />
              <q-btn flat no-caps color="primary" label="Sección A mañana" @click="crearSeccion(g.id, 'A', 'manana')" />
              <q-btn flat no-caps color="negative" label="Borrar" @click="borrarGrado(g)" />
            </q-item-section>
          </q-item>
          <q-item v-for="s in g.secciones" :key="s.id">
            <q-item-section>
              <q-item-label caption>Sección {{ s.letra }} {{ s.turno === 'tarde' ? 'tarde' : 'mañana' }}</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-btn flat no-caps color="negative" label="Quitar sección" @click="borrarSeccion(s)" />
            </q-item-section>
          </q-item>
        </template>
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

function fail(err: unknown, fallback: string) {
  const detail =
    err && typeof err === 'object' && 'response' in err
      ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
      : undefined;
  $q.notify({ type: 'negative', message: detail ?? fallback });
}

function renombrarAnio(anio: Anio) {
  $q.dialog({
    title: 'Renombrar año',
    prompt: { model: anio.nombre, type: 'text' },
    cancel: { flat: true, noCaps: true, label: 'Cancelar' },
    ok: { unelevated: true, noCaps: true, color: 'primary', label: 'Guardar' },
  }).onOk(async (nombre: string) => {
    try {
      await api.patch(`/periodo/anios/${anio.id}`, { nombre: nombre.trim() });
      await cargar();
    } catch (err) {
      fail(err, 'No se pudo renombrar el año');
    }
  });
}

function borrarAnio(anio: Anio) {
  $q.dialog({
    title: 'Borrar año',
    message: 'Solo si no tiene grados ni inscripciones.',
    cancel: { flat: true, noCaps: true, label: 'Cancelar' },
    ok: { unelevated: true, noCaps: true, color: 'negative', label: 'Borrar' },
  }).onOk(async () => {
    try {
      await api.delete(`/periodo/anios/${anio.id}`);
      await cargar();
    } catch (err) {
      fail(err, 'No se pudo borrar el año');
    }
  });
}

function renombrarGrado(g: Grado) {
  $q.dialog({
    title: 'Renombrar grado',
    prompt: { model: g.nombre, type: 'text' },
    cancel: { flat: true, noCaps: true, label: 'Cancelar' },
    ok: { unelevated: true, noCaps: true, color: 'primary', label: 'Guardar' },
  }).onOk(async (nombre: string) => {
    try {
      await api.patch(`/periodo/grados/${g.id}`, { nombre: nombre.trim() });
      await cargar();
    } catch (err) {
      fail(err, 'No se pudo renombrar el grado');
    }
  });
}

function borrarGrado(g: Grado) {
  $q.dialog({
    title: 'Borrar grado',
    message: 'Solo si no tiene secciones ni materias.',
    cancel: { flat: true, noCaps: true, label: 'Cancelar' },
    ok: { unelevated: true, noCaps: true, color: 'negative', label: 'Borrar' },
  }).onOk(async () => {
    try {
      await api.delete(`/periodo/grados/${g.id}`);
      await cargar();
    } catch (err) {
      fail(err, 'No se pudo borrar el grado');
    }
  });
}

function borrarSeccion(s: Seccion) {
  $q.dialog({
    title: 'Quitar sección',
    message: 'Solo si no tiene inscritos, lista ni asignación.',
    cancel: { flat: true, noCaps: true, label: 'Cancelar' },
    ok: { unelevated: true, noCaps: true, color: 'negative', label: 'Borrar' },
  }).onOk(async () => {
    try {
      await api.delete(`/periodo/secciones/${s.id}`);
      await cargar();
    } catch (err) {
      fail(err, 'No se pudo borrar la sección');
    }
  });
}

onMounted(cargar);
</script>
