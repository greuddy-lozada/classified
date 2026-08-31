<template>
  <AppPage title="Docentes" subtitle="Registra al profesor y asígnalo a su sección.">
    <div class="app-card">
      <h2 class="app-card__title">Nuevo docente</h2>
      <q-form class="row q-col-gutter-md" @submit.prevent="registrar">
        <div class="col-12 col-sm-6 col-md-3">
          <q-select v-model="ficha.tipo_doc" outlined emit-value map-options :options="tiposDoc" label="Documento" />
        </div>
        <div class="col-12 col-sm-6 col-md-3">
          <q-input v-model="ficha.numero_doc" outlined label="Número" />
        </div>
        <div class="col-12 col-sm-6 col-md-3">
          <q-input v-model="ficha.nombres" outlined label="Nombres" />
        </div>
        <div class="col-12 col-sm-6 col-md-3">
          <q-input v-model="ficha.apellidos" outlined label="Apellidos" />
        </div>
        <div class="col-12 col-sm-6">
          <q-input v-model="ficha.email" outlined type="email" label="Correo" />
        </div>
        <div class="col-12 col-sm-6">
          <q-input v-model="ficha.password" outlined type="password" label="Clave" />
        </div>
        <div class="col-12">
          <q-btn unelevated type="submit" color="primary" no-caps label="Registrar docente" />
        </div>
      </q-form>
    </div>

    <div v-if="editando" class="app-card">
      <h2 class="app-card__title">Editar ficha</h2>
      <q-form class="row q-col-gutter-md" @submit.prevent="guardarEdicion">
        <div class="col-12 col-sm-6 col-md-3">
          <q-select v-model="editando.tipo_doc" outlined emit-value map-options :options="tiposDoc" label="Documento" />
        </div>
        <div class="col-12 col-sm-6 col-md-3">
          <q-input v-model="editando.numero_doc" outlined label="Número" />
        </div>
        <div class="col-12 col-sm-6 col-md-3">
          <q-input v-model="editando.nombres" outlined label="Nombres" />
        </div>
        <div class="col-12 col-sm-6 col-md-3">
          <q-input v-model="editando.apellidos" outlined label="Apellidos" />
        </div>
        <div class="col-12">
          <q-btn unelevated type="submit" color="primary" no-caps label="Guardar" class="q-mr-sm" />
          <q-btn flat no-caps label="Cancelar" @click="editando = null" />
        </div>
      </q-form>
    </div>

    <div class="app-card">
      <h2 class="app-card__title">Plantel</h2>
      <p v-if="!docentes.length" class="app-empty">Todavía no hay docentes. Regístralos para poder asignarlos.</p>
      <q-list v-else separator>
        <q-item v-for="d in docentes" :key="d.usuario_id">
          <q-item-section>
            <q-item-label>{{ etiquetaDocente(d) }}</q-item-label>
            <q-item-label caption>{{ d.email }}<span v-if="d.numero_doc"> · {{ d.numero_doc }}</span></q-item-label>
          </q-item-section>
          <q-item-section v-if="d.persona_id" side>
            <q-btn flat no-caps color="primary" label="Editar" @click="editar(d)" />
            <q-btn flat no-caps color="negative" label="Borrar" @click="borrar(d)" />
          </q-item-section>
        </q-item>
      </q-list>
    </div>

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
import { computed, reactive, ref, watch } from 'vue';
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
  persona_id: string | null;
  nombres: string;
  apellidos: string;
  tipo_doc: string | null;
  numero_doc: string | null;
}
interface Asignacion {
  id: string;
  usuario_email: string;
  materia_nombre: string | null;
}

const $q = useQuasar();
const auth = useAuthStore();
const esDireccion = computed(() => auth.me?.rol === 'direccion');
const tiposDoc = [
  { label: 'Cédula V', value: 'cedula_v' },
  { label: 'Cédula E', value: 'cedula_e' },
  { label: 'Pasaporte', value: 'pasaporte' },
  { label: 'Expediente', value: 'expediente' },
];
const ficha = reactive({
  tipo_doc: 'cedula_v',
  numero_doc: '',
  nombres: '',
  apellidos: '',
  email: '',
  password: '',
});
const editando = ref<Docente | null>(null);

function etiquetaDocente(d: Docente) {
  const nombre = `${d.nombres} ${d.apellidos}`.trim();
  return nombre || d.email;
}
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
const docenteOptions = computed(() =>
  docentes.value.map((d) => ({ label: etiquetaDocente(d), value: d.usuario_id })),
);

async function cargarDocentes() {
  const { data } = await api.get<Docente[]>('/evaluacion/docentes');
  docentes.value = data;
  if (!usuarioId.value && data[0]) usuarioId.value = data[0].usuario_id;
}

async function cargarAnios() {
  const { data: anioData } = await api.get<Anio[]>('/periodo/anios');
  anios.value = anioData;
  if (!anioId.value && anioData[0]) anioId.value = anioData[0].id;
  await cargarDocentes();
}

async function registrar() {
  try {
    await api.post('/personas/docentes', { ...ficha });
    ficha.numero_doc = '';
    ficha.nombres = '';
    ficha.apellidos = '';
    ficha.email = '';
    await cargarDocentes();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo registrar el docente' });
  }
}

function editar(d: Docente) {
  editando.value = { ...d };
}

async function guardarEdicion() {
  if (!editando.value?.persona_id || !editando.value.tipo_doc) return;
  try {
    await api.patch(`/personas/${editando.value.persona_id}`, {
      tipo_doc: editando.value.tipo_doc,
      numero_doc: editando.value.numero_doc,
      nombres: editando.value.nombres,
      apellidos: editando.value.apellidos,
    });
    editando.value = null;
    await cargarDocentes();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo editar' });
  }
}

function borrar(d: Docente) {
  if (!d.persona_id) return;
  $q.dialog({
    title: 'Borrar docente',
    message: 'Solo si no tiene sección asignada.',
    cancel: { flat: true, noCaps: true, label: 'Cancelar' },
    ok: { unelevated: true, noCaps: true, color: 'negative', label: 'Borrar' },
  }).onOk(async () => {
    try {
      await api.delete(`/personas/${d.persona_id}`);
      await cargarDocentes();
    } catch {
      $q.notify({ type: 'negative', message: 'No se pudo borrar: tiene asignación' });
    }
  });
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
