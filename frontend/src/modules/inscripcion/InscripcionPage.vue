<template>
  <q-page class="q-pa-lg">
    <div class="text-h5 q-mb-md">Inscripciones</div>

    <div class="row q-col-gutter-sm q-mb-md">
      <div class="col-6">
        <q-select v-model="anioId" outlined dense :options="anioOptions" label="Año escolar" emit-value map-options />
      </div>
      <div class="col-6">
        <q-select v-model="seccionId" outlined dense :options="seccionOptions" label="Sección a asignar" emit-value map-options />
      </div>
    </div>

    <q-form class="row q-col-gutter-sm q-mb-lg" @submit.prevent="solicitarCupo">
      <div class="col-8">
        <q-select
          v-model="alumnoId"
          outlined
          dense
          :options="alumnoOptions"
          label="Alumno (ficha)"
          emit-value
          map-options
        />
      </div>
      <div class="col-4">
        <q-btn type="submit" color="primary" label="Solicitar cupo" class="full-width" />
      </div>
    </q-form>

    <q-list bordered separator>
      <q-item v-for="ins in lista" :key="ins.id">
        <q-item-section>
          <q-item-label>{{ ins.alumno_nombres }} {{ ins.alumno_apellidos }}</q-item-label>
          <q-item-label caption>
            {{ ins.estado }} · matrícula {{ ins.estado_matricula }}
            · {{ ins.recaudos_pendientes ? 'recaudos pendientes' : 'recaudos ok' }}
          </q-item-label>
        </q-item-section>
        <q-item-section side>
          <q-btn
            v-if="ins.estado === 'preinscrito'"
            dense
            flat
            label="Asignar sección"
            @click="asignar(ins.id)"
          />
        </q-item-section>
      </q-item>
    </q-list>
  </q-page>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useQuasar } from 'quasar';
import { api } from 'src/boot/axios';

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
interface Inscripcion {
  id: string;
  alumno_nombres: string;
  alumno_apellidos: string;
  estado: string;
  estado_matricula: string;
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

watch(anioId, () => {
  seccionId.value = null;
  void cargarAnio();
});
void cargar();
</script>
