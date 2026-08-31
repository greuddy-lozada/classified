<template>
  <AppPage title="Docentes" subtitle="Asigna quién carga notas y pasa lista en cada sección.">
    <div v-if="esDireccion" class="app-card">
      <h2 class="app-card__title">Nueva asignación</h2>
      <q-form class="row q-col-gutter-md" @submit.prevent="crear">
        <div class="col-12 col-sm-4">
          <q-select v-model="anioId" outlined emit-value map-options :options="anioOptions" label="Año" />
        </div>
        <div class="col-12 col-sm-4">
          <q-select v-model="seccionId" outlined emit-value map-options :options="seccionOptions" label="Sección" />
        </div>
        <div class="col-12 col-sm-4">
          <q-select v-model="usuarioId" outlined emit-value map-options :options="docenteOptions" label="Docente" />
        </div>
        <div v-if="esquema === 'numerico'" class="col-12 col-sm-6">
          <q-select v-model="materiaId" outlined emit-value map-options :options="materiaOptions" label="Materia" />
        </div>
        <div class="col-12">
          <q-btn unelevated type="submit" color="primary" no-caps label="Asignar" />
        </div>
      </q-form>
    </div>

    <div class="app-card">
      <h2 class="app-card__title">De esta sección</h2>
      <p v-if="!lista.length" class="app-empty">Nadie asignado a esta sección.</p>
      <q-list v-else separator>
        <q-item v-for="a in lista" :key="a.id">
          <q-item-section>
            <q-item-label>{{ a.usuario_email }}</q-item-label>
            <q-item-label caption>{{ a.materia_nombre || 'Lista de la sección' }}</q-item-label>
          </q-item-section>
          <q-item-section side>
            <q-btn v-if="esDireccion" flat no-caps color="negative" label="Quitar" @click="quitar(a.id)" />
          </q-item-section>
        </q-item>
      </q-list>
    </div>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useQuasar } from 'quasar';
import { api } from 'src/boot/axios';
import { useAuthStore } from 'src/stores/auth';
import AppPage from '../dashboard/AppPage.vue';

interface Anio {
  id: string;
  nombre: string;
}
interface Grado {
  id: string;
  nombre: string;
  esquema_evaluacion: string;
  secciones: { id: string; letra: string; turno: string }[];
}
interface Materia {
  id: string;
  nombre: string;
}
interface Docente {
  usuario_id: string;
  email: string;
}
interface Asignacion {
  id: string;
  usuario_email: string;
  materia_nombre: string | null;
}

const $q = useQuasar();
const auth = useAuthStore();
const esDireccion = computed(() => auth.me?.rol === 'direccion');
const anios = ref<Anio[]>([]);
const grados = ref<Grado[]>([]);
const materias = ref<Materia[]>([]);
const docentes = ref<Docente[]>([]);
const lista = ref<Asignacion[]>([]);
const anioId = ref<string | null>(null);
const seccionId = ref<string | null>(null);
const usuarioId = ref<string | null>(null);
const materiaId = ref<string | null>(null);

const anioOptions = computed(() => anios.value.map((a) => ({ label: a.nombre, value: a.id })));
const seccionOptions = computed(() =>
  grados.value.flatMap((g) =>
    g.secciones.map((s) => ({ label: `${g.nombre} ${s.letra} ${s.turno}`, value: s.id })),
  ),
);
const gradoActual = computed(() => grados.value.find((g) => g.secciones.some((s) => s.id === seccionId.value)));
const esquema = computed(() => gradoActual.value?.esquema_evaluacion ?? null);
const materiaOptions = computed(() => materias.value.map((m) => ({ label: m.nombre, value: m.id })));
const docenteOptions = computed(() => docentes.value.map((d) => ({ label: d.email, value: d.usuario_id })));

async function cargarAnios() {
  const [{ data: anioData }, { data: docData }] = await Promise.all([
    api.get<Anio[]>('/periodo/anios'),
    api.get<Docente[]>('/evaluacion/docentes'),
  ]);
  anios.value = anioData;
  docentes.value = docData;
  if (!anioId.value && anioData[0]) anioId.value = anioData[0].id;
  if (!usuarioId.value && docData[0]) usuarioId.value = docData[0].usuario_id;
}

async function cargarCatalogo() {
  grados.value = [];
  seccionId.value = null;
  if (!anioId.value) return;
  const { data } = await api.get<Grado[]>('/periodo/grados', { params: { anio_escolar_id: anioId.value } });
  grados.value = data;
  if (seccionOptions.value[0]) seccionId.value = seccionOptions.value[0].value;
}

async function cargarSeccion() {
  lista.value = [];
  materias.value = [];
  materiaId.value = null;
  if (!seccionId.value) return;
  const { data } = await api.get<Asignacion[]>('/evaluacion/asignaciones', { params: { seccion_id: seccionId.value } });
  lista.value = data;
  if (gradoActual.value?.esquema_evaluacion === 'numerico') {
    const m = await api.get<Materia[]>('/evaluacion/materias', { params: { grado_id: gradoActual.value.id } });
    materias.value = m.data;
    if (m.data[0]) materiaId.value = m.data[0].id;
  }
}

async function crear() {
  if (!seccionId.value || !usuarioId.value) return;
  try {
    await api.post('/evaluacion/asignaciones', {
      usuario_id: usuarioId.value,
      seccion_id: seccionId.value,
      materia_id: esquema.value === 'numerico' ? materiaId.value : null,
    });
    await cargarSeccion();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo asignar' });
  }
}

async function quitar(id: string) {
  try {
    await api.delete(`/evaluacion/asignaciones/${id}`);
    await cargarSeccion();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo quitar' });
  }
}

watch(anioId, cargarCatalogo);
watch(seccionId, cargarSeccion);
void cargarAnios();
</script>
