<template>
  <AppPage title="Materias" subtitle="Pensum por grado. Solo grados con nota 1–20.">
    <div class="app-card">
      <h2 class="app-card__title">Nueva materia</h2>
      <q-form class="row q-col-gutter-md" @submit.prevent="crear">
        <div class="col-12 col-sm-4">
          <q-select v-model="anioId" outlined emit-value map-options :options="anioOptions" label="Año" />
        </div>
        <div class="col-12 col-sm-4">
          <q-select v-model="gradoId" outlined emit-value map-options :options="gradoOptions" label="Grado" />
        </div>
        <div class="col-12 col-sm-4">
          <q-input v-model="nombre" outlined label="Nombre (ej. Matemática)" />
        </div>
        <div class="col-12">
          <q-btn unelevated type="submit" color="primary" no-caps label="Crear materia" />
        </div>
      </q-form>
    </div>

    <div class="app-card">
      <h2 class="app-card__title">Del grado</h2>
      <p v-if="!gradoId" class="app-empty">Elige un grado numérico para ver el pensum.</p>
      <p v-else-if="!materias.length" class="app-empty">Este grado aún no tiene materias.</p>
      <q-list v-else separator>
        <q-item v-for="m in materias" :key="m.id">
          <q-item-section>
            <q-item-label>{{ m.nombre }}</q-item-label>
          </q-item-section>
          <q-item-section side>
            <q-btn flat no-caps color="primary" label="Renombrar" @click="renombrar(m)" />
            <q-btn flat no-caps color="negative" label="Borrar" @click="borrar(m)" />
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
import AppPage from '../dashboard/AppPage.vue';

interface Anio {
  id: string;
  nombre: string;
}
interface Grado {
  id: string;
  nombre: string;
  nivel: string;
  esquema_evaluacion: string;
}
interface Materia {
  id: string;
  nombre: string;
}

const $q = useQuasar();
const anios = ref<Anio[]>([]);
const grados = ref<Grado[]>([]);
const materias = ref<Materia[]>([]);
const anioId = ref<string | null>(null);
const gradoId = ref<string | null>(null);
const nombre = ref('');

const anioOptions = computed(() => anios.value.map((a) => ({ label: a.nombre, value: a.id })));
const gradoOptions = computed(() =>
  grados.value
    .filter((g) => g.esquema_evaluacion === 'numerico')
    .map((g) => ({ label: `${g.nombre} (${g.nivel})`, value: g.id })),
);

async function cargarAnios() {
  const { data } = await api.get<Anio[]>('/periodo/anios');
  anios.value = data;
  if (!anioId.value && data[0]) anioId.value = data[0].id;
}

async function cargarGrados() {
  grados.value = [];
  gradoId.value = null;
  if (!anioId.value) return;
  const { data } = await api.get<Grado[]>('/periodo/grados', { params: { anio_escolar_id: anioId.value } });
  grados.value = data;
  if (gradoOptions.value[0]) gradoId.value = gradoOptions.value[0].value;
}

async function cargarMaterias() {
  materias.value = [];
  if (!gradoId.value) return;
  const { data } = await api.get<Materia[]>('/evaluacion/materias', { params: { grado_id: gradoId.value } });
  materias.value = data;
}

async function crear() {
  if (!gradoId.value || !nombre.value.trim()) return;
  try {
    await api.post('/evaluacion/materias', { grado_id: gradoId.value, nombre: nombre.value.trim() });
    nombre.value = '';
    await cargarMaterias();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo crear la materia' });
  }
}

function renombrar(m: Materia) {
  $q.dialog({
    title: 'Renombrar',
    prompt: { model: m.nombre, type: 'text' },
    cancel: { flat: true, noCaps: true, label: 'Cancelar' },
    ok: { unelevated: true, noCaps: true, color: 'primary', label: 'Guardar' },
  }).onOk(async (value: string) => {
    const next = value.trim();
    if (!next) return;
    try {
      await api.patch(`/evaluacion/materias/${m.id}`, { nombre: next });
      await cargarMaterias();
    } catch {
      $q.notify({ type: 'negative', message: 'No se pudo renombrar' });
    }
  });
}

function borrar(m: Materia) {
  $q.dialog({
    title: 'Borrar materia',
    message: `¿Quitar ${m.nombre} de este grado?`,
    cancel: { flat: true, noCaps: true, label: 'Cancelar' },
    ok: { unelevated: true, noCaps: true, color: 'negative', label: 'Borrar' },
  }).onOk(async () => {
    try {
      await api.delete(`/evaluacion/materias/${m.id}`);
      await cargarMaterias();
    } catch {
      $q.notify({ type: 'negative', message: 'No se puede borrar: tiene notas, lista o asignación' });
    }
  });
}

watch(anioId, cargarGrados);
watch(gradoId, cargarMaterias);
void cargarAnios();
</script>
