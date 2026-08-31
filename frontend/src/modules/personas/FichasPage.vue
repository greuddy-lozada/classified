<template>
  <AppPage title="Fichas" subtitle="Registra alumnos y el representante que firma.">
    <div class="app-card">
      <h2 class="app-card__title">Alumno</h2>
      <q-form class="row q-col-gutter-md" @submit.prevent="crearAlumno">
        <div class="col-12 col-sm-6 col-md-3">
          <q-select v-model="alumno.tipo_doc" outlined emit-value map-options :options="tiposDoc" label="Documento" />
        </div>
        <div class="col-12 col-sm-6 col-md-3">
          <q-input v-model="alumno.numero_doc" outlined label="Número" />
        </div>
        <div class="col-12 col-sm-6 col-md-3">
          <q-input v-model="alumno.nombres" outlined label="Nombres" />
        </div>
        <div class="col-12 col-sm-6 col-md-3">
          <q-input v-model="alumno.apellidos" outlined label="Apellidos" />
        </div>
        <div class="col-12">
          <q-btn unelevated type="submit" color="primary" no-caps label="Registrar alumno" />
        </div>
      </q-form>
    </div>

    <div class="app-card">
      <h2 class="app-card__title">Representante</h2>
      <q-form class="row q-col-gutter-md" @submit.prevent="crearRepresentante">
        <div class="col-12 col-md-6">
          <q-select v-model="rep.alumno_id" outlined emit-value map-options :options="alumnoOptions" label="Alumno" />
        </div>
        <div class="col-12 col-sm-6 col-md-3">
          <q-select v-model="rep.parentesco" outlined emit-value map-options :options="parentescos" label="Parentesco" />
        </div>
        <div class="col-12 col-sm-6 col-md-3">
          <q-select v-model="rep.tipo_doc" outlined emit-value map-options :options="tiposDoc" label="Documento" />
        </div>
        <div class="col-12 col-sm-6 col-md-3">
          <q-input v-model="rep.numero_doc" outlined label="Número" />
        </div>
        <div class="col-12 col-sm-6 col-md-3">
          <q-input v-model="rep.nombres" outlined label="Nombres" />
        </div>
        <div class="col-12 col-sm-6 col-md-3">
          <q-input v-model="rep.apellidos" outlined label="Apellidos" />
        </div>
        <div class="col-12 col-sm-6 col-md-3">
          <q-input v-model="rep.email" outlined type="email" label="Correo" />
        </div>
        <div class="col-12 col-sm-6 col-md-3">
          <q-input v-model="rep.password" outlined type="password" label="Clave" />
        </div>
        <div class="col-12">
          <q-btn unelevated type="submit" color="primary" no-caps label="Registrar representante" />
        </div>
      </q-form>
    </div>

    <div class="app-card">
      <h2 class="app-card__title">Personas</h2>
      <p v-if="!lista.length" class="app-empty">Todavía no hay fichas en este plantel.</p>
      <q-list v-else separator>
        <q-item v-for="p in lista" :key="p.id">
          <q-item-section>
            <q-item-label>{{ p.nombres }} {{ p.apellidos }}</q-item-label>
            <q-item-label caption>{{ p.es_alumno ? 'Alumno' : 'Representante' }} · {{ p.numero_doc }}</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </div>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { useQuasar } from 'quasar';
import { api } from 'src/boot/axios';
import AppPage from '../dashboard/AppPage.vue';

interface Persona {
  id: string;
  alumno_id: string | null;
  nombres: string;
  apellidos: string;
  numero_doc: string;
  es_alumno: boolean;
}

const $q = useQuasar();
const lista = ref<Persona[]>([]);
const tiposDoc = [
  { label: 'Partida', value: 'partida' },
  { label: 'Cédula V', value: 'cedula_v' },
  { label: 'Cédula E', value: 'cedula_e' },
  { label: 'Pasaporte', value: 'pasaporte' },
  { label: 'Expediente', value: 'expediente' },
];
const parentescos = [
  { label: 'Madre', value: 'madre' },
  { label: 'Padre', value: 'padre' },
  { label: 'Abuelo', value: 'abuelo' },
  { label: 'Tutor', value: 'tutor' },
];
const alumno = reactive({ tipo_doc: 'partida', numero_doc: '', nombres: '', apellidos: '' });
const rep = reactive({
  alumno_id: null as string | null,
  parentesco: 'madre',
  tipo_doc: 'cedula_v',
  numero_doc: '',
  nombres: '',
  apellidos: '',
  email: '',
  password: '',
});

const alumnoOptions = computed(() =>
  lista.value
    .filter((p) => p.es_alumno && p.alumno_id)
    .map((p) => ({ label: `${p.nombres} ${p.apellidos}`, value: p.alumno_id })),
);

async function cargar() {
  const { data } = await api.get<Persona[]>('/personas');
  lista.value = data;
}

async function crearAlumno() {
  try {
    await api.post('/personas/alumnos', { ...alumno });
    alumno.numero_doc = '';
    alumno.nombres = '';
    alumno.apellidos = '';
    await cargar();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo registrar el alumno' });
  }
}

async function crearRepresentante() {
  if (!rep.alumno_id) return;
  try {
    await api.post('/personas/representantes', { ...rep, es_principal: true });
    rep.numero_doc = '';
    rep.nombres = '';
    rep.apellidos = '';
    rep.email = '';
    await cargar();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo registrar el representante' });
  }
}

onMounted(cargar);
</script>
