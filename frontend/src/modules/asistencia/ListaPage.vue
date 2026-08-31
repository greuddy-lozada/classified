<template>
  <q-page class="q-pa-lg">
    <div class="text-h5 q-mb-md">Asistencia</div>
    <div class="row q-col-gutter-sm q-mb-md">
      <div class="col-4">
        <q-select v-model="anioId" outlined dense emit-value map-options :options="anioOptions" label="Año" />
      </div>
      <div class="col-4">
        <q-select v-model="seccionId" outlined dense emit-value map-options :options="seccionOptions" label="Sección" />
      </div>
      <div class="col-4">
        <q-input v-model="fecha" outlined dense type="date" label="Fecha" />
      </div>
      <div v-if="esquema === 'numerico'" class="col-6">
        <q-select v-model="materiaId" outlined dense emit-value map-options :options="materiaOptions" label="Materia" />
      </div>
      <div class="col-12">
        <q-btn color="primary" label="Cargar lista" @click="cargarLista" />
      </div>
    </div>
    <q-list bordered separator>
      <q-item v-for="item in lista" :key="item.inscripcion_id">
        <q-item-section>
          {{ item.alumno_nombres }} {{ item.alumno_apellidos }}
        </q-item-section>
        <q-item-section side>
          <q-btn-toggle
            :model-value="item.estado"
            unelevated
            dense
            :options="estados"
            @update:model-value="(v) => marcar(item.inscripcion_id, v)"
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
  esquema_evaluacion: string;
  secciones: { id: string; letra: string; turno: string }[];
}
interface Materia {
  id: string;
  nombre: string;
}
interface Item {
  inscripcion_id: string;
  alumno_nombres: string;
  alumno_apellidos: string;
  estado: string | null;
}

const $q = useQuasar();
const anios = ref<Anio[]>([]);
const grados = ref<Grado[]>([]);
const materias = ref<Materia[]>([]);
const anioId = ref<string | null>(null);
const seccionId = ref<string | null>(null);
const materiaId = ref<string | null>(null);
const fecha = ref(new Date().toISOString().slice(0, 10));
const lista = ref<Item[]>([]);
const estados = [
  { label: 'P', value: 'presente' },
  { label: 'A', value: 'ausente' },
  { label: 'J', value: 'justificado' },
  { label: 'T', value: 'tardanza' },
];

const anioOptions = computed(() => anios.value.map((a) => ({ label: a.nombre, value: a.id })));
const seccionOptions = computed(() =>
  grados.value.flatMap((g) =>
    g.secciones.map((s) => ({ label: `${g.nombre} ${s.letra} ${s.turno}`, value: s.id })),
  ),
);
const gradoActual = computed(() =>
  grados.value.find((g) => g.secciones.some((s) => s.id === seccionId.value)),
);
const esquema = computed(() => gradoActual.value?.esquema_evaluacion ?? null);
const materiaOptions = computed(() => materias.value.map((m) => ({ label: m.nombre, value: m.id })));

async function cargarAnios() {
  const { data } = await api.get<Anio[]>('/periodo/anios');
  anios.value = data;
  if (!anioId.value && data[0]) anioId.value = data[0].id;
}

async function cargarGrados() {
  if (!anioId.value) return;
  const { data } = await api.get<Grado[]>('/periodo/grados', { params: { anio_escolar_id: anioId.value } });
  grados.value = data;
  if (!seccionId.value && seccionOptions.value[0]) seccionId.value = seccionOptions.value[0].value;
}

async function cargarMaterias() {
  materias.value = [];
  materiaId.value = null;
  if (!gradoActual.value || gradoActual.value.esquema_evaluacion !== 'numerico') return;
  const { data } = await api.get<Materia[]>('/evaluacion/materias', { params: { grado_id: gradoActual.value.id } });
  materias.value = data;
  if (data[0]) materiaId.value = data[0].id;
}

async function cargarLista() {
  if (!seccionId.value) return;
  try {
    const { data } = await api.get<Item[]>('/asistencia/lista', {
      params: {
        seccion_id: seccionId.value,
        fecha: fecha.value,
        materia_id: esquema.value === 'numerico' ? materiaId.value || undefined : undefined,
      },
    });
    lista.value = data;
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo cargar la lista' });
  }
}

async function marcar(inscripcionId: string, estado: string) {
  try {
    await api.put('/asistencia', {
      inscripcion_id: inscripcionId,
      fecha: fecha.value,
      estado,
      materia_id: esquema.value === 'numerico' ? materiaId.value : null,
    });
    await cargarLista();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo marcar' });
  }
}

watch(anioId, async () => {
  seccionId.value = null;
  await cargarGrados();
});
watch(seccionId, cargarMaterias);
void cargarAnios();
</script>
