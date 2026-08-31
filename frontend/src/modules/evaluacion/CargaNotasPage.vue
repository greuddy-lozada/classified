<template>
  <q-page class="q-pa-lg">
    <div class="text-h5 q-mb-md">Carga de evaluación</div>
    <div class="row q-col-gutter-sm q-mb-md">
      <div class="col-4">
        <q-select v-model="anioId" outlined dense emit-value map-options :options="anioOptions" label="Año" />
      </div>
      <div class="col-4">
        <q-select v-model="seccionId" outlined dense emit-value map-options :options="seccionOptions" label="Sección" />
      </div>
      <div class="col-4">
        <q-select v-model="lapsoId" outlined dense emit-value map-options :options="lapsoOptions" label="Lapso" />
      </div>
      <div class="col-8">
        <q-select v-model="inscripcionId" outlined dense emit-value map-options :options="alumnoOptions" label="Alumno" />
      </div>
      <div class="col-4">
        <q-btn
          v-if="inscripcionId"
          outline
          color="primary"
          label="Ver boletín"
          class="full-width"
          :to="`/dashboard/boletines/${inscripcionId}`"
        />
      </div>
    </div>

    <q-form v-if="esquema === 'numerico'" class="row q-col-gutter-sm q-mb-md" @submit.prevent="cargarNota">
      <div class="col-5">
        <q-select v-model="materiaId" outlined dense emit-value map-options :options="materiaOptions" label="Materia" />
      </div>
      <div class="col-3">
        <q-input v-model="nuevaMateria" outlined dense label="Nueva materia" />
      </div>
      <div class="col-2">
        <q-btn outline color="secondary" label="Crear" class="full-width" @click="crearMateria" />
      </div>
      <div class="col-2">
        <q-input v-model.number="valor" outlined dense type="number" label="Nota 1-20" />
      </div>
      <div class="col-12">
        <q-btn type="submit" color="primary" label="Guardar nota" />
      </div>
    </q-form>

    <q-form v-else-if="esquema === 'informe'" class="row q-col-gutter-sm" @submit.prevent="cargarInforme">
      <div class="col-4">
        <q-select v-model="area" outlined dense :options="areas" label="Área" />
      </div>
      <div class="col-4">
        <q-select v-model="juicio" outlined dense :options="juicios" label="Juicio" />
      </div>
      <div class="col-4">
        <q-input v-model="comentario" outlined dense label="Comentario" />
      </div>
      <div class="col-12">
        <q-btn type="submit" color="secondary" label="Guardar informe" />
      </div>
    </q-form>
  </q-page>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useQuasar } from 'quasar';
import { api } from 'src/boot/axios';

interface Lapso {
  id: string;
  nombre: string;
}
interface Anio {
  id: string;
  nombre: string;
  lapsos: Lapso[];
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
interface Inscripcion {
  id: string;
  seccion_id: string | null;
  alumno_nombres: string;
  alumno_apellidos: string;
}

const $q = useQuasar();
const anios = ref<Anio[]>([]);
const grados = ref<Grado[]>([]);
const materias = ref<Materia[]>([]);
const inscritos = ref<Inscripcion[]>([]);
const anioId = ref<string | null>(null);
const seccionId = ref<string | null>(null);
const inscripcionId = ref<string | null>(null);
const lapsoId = ref<string | null>(null);
const materiaId = ref<string | null>(null);
const nuevaMateria = ref('');
const valor = ref(10);
const area = ref('lenguaje');
const juicio = ref('en_proceso');
const comentario = ref('');
const areas = ['lenguaje', 'socioemocional', 'psicomotor', 'exploracion'];
const juicios = ['logrado', 'en_proceso', 'iniciado'];

const anioOptions = computed(() => anios.value.map((a) => ({ label: a.nombre, value: a.id })));
const anioActual = computed(() => anios.value.find((a) => a.id === anioId.value));
const lapsoOptions = computed(() => (anioActual.value?.lapsos ?? []).map((l) => ({ label: l.nombre, value: l.id })));
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
const alumnoOptions = computed(() =>
  inscritos.value
    .filter((i) => i.seccion_id === seccionId.value)
    .map((i) => ({ label: `${i.alumno_nombres} ${i.alumno_apellidos}`, value: i.id })),
);

async function cargarAnios() {
  const { data } = await api.get<Anio[]>('/periodo/anios');
  anios.value = data;
  if (!anioId.value && data[0]) anioId.value = data[0].id;
}

async function cargarCatalogo() {
  if (!anioId.value) return;
  const [g, ins] = await Promise.all([
    api.get<Grado[]>('/periodo/grados', { params: { anio_escolar_id: anioId.value } }),
    api.get<Inscripcion[]>('/inscripciones', { params: { anio_escolar_id: anioId.value } }),
  ]);
  grados.value = g.data;
  inscritos.value = ins.data;
  if (!seccionId.value && seccionOptions.value[0]) seccionId.value = seccionOptions.value[0].value;
  if (!lapsoId.value && lapsoOptions.value[0]) lapsoId.value = lapsoOptions.value[0].value;
}

async function cargarMaterias() {
  materias.value = [];
  materiaId.value = null;
  if (!gradoActual.value || gradoActual.value.esquema_evaluacion !== 'numerico') return;
  const { data } = await api.get<Materia[]>('/evaluacion/materias', { params: { grado_id: gradoActual.value.id } });
  materias.value = data;
  if (data[0]) materiaId.value = data[0].id;
}

async function crearMateria() {
  if (!gradoActual.value || !nuevaMateria.value) return;
  try {
    await api.post('/evaluacion/materias', { grado_id: gradoActual.value.id, nombre: nuevaMateria.value });
    nuevaMateria.value = '';
    await cargarMaterias();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo crear la materia' });
  }
}

async function cargarNota() {
  if (!inscripcionId.value || !lapsoId.value || !materiaId.value) return;
  try {
    await api.post('/evaluacion/notas', {
      inscripcion_id: inscripcionId.value,
      lapso_id: lapsoId.value,
      materia_id: materiaId.value,
      valor: valor.value,
    });
    $q.notify({ type: 'positive', message: 'Nota guardada' });
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo guardar la nota' });
  }
}

async function cargarInforme() {
  if (!inscripcionId.value || !lapsoId.value) return;
  try {
    await api.post('/evaluacion/informes', {
      inscripcion_id: inscripcionId.value,
      lapso_id: lapsoId.value,
      area: area.value,
      juicio: juicio.value,
      comentario: comentario.value,
    });
    $q.notify({ type: 'positive', message: 'Informe guardado' });
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo guardar el informe' });
  }
}

watch(anioId, async () => {
  seccionId.value = null;
  inscripcionId.value = null;
  lapsoId.value = null;
  await cargarCatalogo();
});
watch(seccionId, async () => {
  inscripcionId.value = alumnoOptions.value[0]?.value ?? null;
  await cargarMaterias();
});
void cargarAnios();
</script>
