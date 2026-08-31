<template>
  <AppPage title="Inscripciones" subtitle="Cupo, sección, recaudos y retiro. Activa para que salga en la lista.">
    <div class="app-card">
      <q-form class="row q-col-gutter-md" @submit.prevent="solicitarCupo">
        <div class="col-12 col-sm-6">
          <q-select v-model="anioId" outlined emit-value map-options :options="anioOptions" label="Año escolar" />
        </div>
        <div class="col-12 col-sm-6">
          <q-select v-model="seccionId" outlined emit-value map-options :options="seccionOptions" label="Sección a asignar" />
        </div>
        <div class="col-12 col-sm-8">
          <q-select v-model="alumnoId" outlined emit-value map-options :options="alumnoOptions" label="Alumno" />
        </div>
        <div class="col-12 col-sm-4">
          <q-btn unelevated type="submit" color="primary" no-caps label="Solicitar cupo" class="full-width" />
        </div>
      </q-form>
    </div>
    <div class="app-card">
      <h2 class="app-card__title">Lista</h2>
      <p v-if="!lista.length" class="app-empty">No hay inscripciones en este año.</p>
      <q-list v-else separator>
        <q-item v-for="ins in lista" :key="ins.id" class="column items-stretch q-py-md">
          <div class="row items-center">
            <q-item-section>
              <q-item-label>{{ ins.alumno_nombres }} {{ ins.alumno_apellidos }}</q-item-label>
              <q-item-label caption>
                {{ etiquetaEstado(ins.estado) }} · matrícula {{ etiquetaPago(ins.estado_matricula) }}
              </q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-btn
                v-if="ins.estado === 'preinscrito'"
                unelevated
                no-caps
                color="primary"
                label="Asignar sección"
                @click="asignar(ins.id)"
              />
              <q-btn
                v-if="ins.estado === 'inscrito'"
                unelevated
                no-caps
                color="primary"
                label="Activar"
                @click="activar(ins.id)"
              />
              <q-btn
                v-if="ins.estado !== 'retirado'"
                flat
                no-caps
                color="negative"
                label="Retirar"
                @click="retirar(ins.id)"
              />
            </q-item-section>
          </div>
          <div class="q-gutter-xs q-mt-sm">
            <q-btn
              v-for="r in ins.recaudos"
              :key="r.tipo"
              unelevated
              no-caps
              size="sm"
              :color="r.estado === 'entregado' ? 'primary' : 'grey-5'"
              :text-color="r.estado === 'entregado' ? 'white' : 'dark'"
              :label="etiquetaRecaudo(r.tipo)"
              :disable="ins.estado === 'retirado'"
              @click="toggleRecaudo(ins.id, r)"
            />
          </div>
        </q-item>
      </q-list>
    </div>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useQuasar } from 'quasar';
import { api } from 'src/boot/axios';
import AppPage from '../dashboard/AppPage.vue';

function etiquetaEstado(v: string) {
  const map: Record<string, string> = {
    preinscrito: 'Preinscrito',
    inscrito: 'Inscrito',
    activo: 'Activo',
    retirado: 'Retirado',
  };
  return map[v] ?? v;
}
function etiquetaPago(v: string) {
  const map: Record<string, string> = { pendiente: 'pendiente', pagada: 'pagada', morosa: 'morosa' };
  return map[v] ?? v;
}
function etiquetaRecaudo(v: string) {
  const map: Record<string, string> = {
    partida: 'Partida',
    fotos: 'Fotos',
    cedula_representante: 'Cédula representante',
    cedula_alumno: 'Cédula alumno',
  };
  return map[v] ?? v;
}

interface Anio {
  id: string;
  nombre: string;
}
interface Grado {
  id: string;
  nombre: string;
  secciones: { id: string; letra: string; turno: string }[];
}
interface Persona {
  id: string;
  alumno_id: string | null;
  nombres: string;
  apellidos: string;
  es_alumno: boolean;
}
interface Recaudo {
  tipo: string;
  estado: string;
}
interface Inscripcion {
  id: string;
  alumno_nombres: string;
  alumno_apellidos: string;
  estado: string;
  estado_matricula: string;
  recaudos: Recaudo[];
  recaudos_pendientes: boolean;
}

const $q = useQuasar();
const anios = ref<Anio[]>([]);
const grados = ref<Grado[]>([]);
const anioId = ref<string | null>(null);
const seccionId = ref<string | null>(null);
const personas = ref<Persona[]>([]);
const lista = ref<Inscripcion[]>([]);
const alumnoId = ref<string | null>(null);

const anioOptions = computed(() => anios.value.map((a) => ({ label: a.nombre, value: a.id })));
const seccionOptions = computed(() =>
  grados.value.flatMap((g) =>
    g.secciones.map((s) => ({ label: `${g.nombre} ${s.letra} ${s.turno}`, value: s.id })),
  ),
);
const alumnoOptions = computed(() =>
  personas.value
    .filter((p) => p.es_alumno && p.alumno_id)
    .map((p) => ({ label: `${p.nombres} ${p.apellidos}`, value: p.alumno_id })),
);

async function cargar() {
  const { data } = await api.get<Anio[]>('/periodo/anios');
  anios.value = data;
  if (!anioId.value && data[0]) anioId.value = data[0].id;
  const pers = await api.get<Persona[]>('/personas');
  personas.value = pers.data;
  await cargarAnio();
}

async function cargarAnio() {
  if (!anioId.value) return;
  const [ins, g] = await Promise.all([
    api.get<Inscripcion[]>('/inscripciones', { params: { anio_escolar_id: anioId.value } }),
    api.get<Grado[]>('/periodo/grados', { params: { anio_escolar_id: anioId.value } }),
  ]);
  lista.value = ins.data;
  grados.value = g.data;
  if (!seccionId.value && seccionOptions.value[0]) seccionId.value = seccionOptions.value[0].value;
}

async function solicitarCupo() {
  if (!alumnoId.value || !anioId.value) return;
  try {
    await api.post('/inscripciones', { alumno_id: alumnoId.value, anio_escolar_id: anioId.value });
    await cargar();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo solicitar el cupo' });
  }
}

async function asignar(id: string) {
  const sid = seccionId.value;
  if (!sid) {
    $q.notify({ type: 'warning', message: 'Elige una sección' });
    return;
  }
  try {
    await api.post(`/inscripciones/${id}/seccion`, { seccion_id: sid });
    await cargar();
  } catch (err: unknown) {
    const detail =
      err && typeof err === 'object' && 'response' in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : undefined;
    $q.notify({ type: 'negative', message: detail ?? 'No se pudo asignar sección' });
  }
}

async function activar(id: string) {
  try {
    await api.post(`/inscripciones/${id}/activar`);
    await cargar();
  } catch {
    $q.notify({ type: 'negative', message: 'Debe estar inscrito en una sección' });
  }
}

async function retirar(id: string) {
  try {
    await api.post(`/inscripciones/${id}/retirar`);
    await cargar();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo retirar' });
  }
}

async function toggleRecaudo(id: string, r: Recaudo) {
  const estado = r.estado === 'entregado' ? 'faltante' : 'entregado';
  try {
    await api.patch(`/inscripciones/${id}/recaudos`, { tipo: r.tipo, estado });
    await cargar();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo marcar el recaudo' });
  }
}

watch(anioId, () => {
  seccionId.value = null;
  void cargarAnio();
});
void cargar();
</script>
