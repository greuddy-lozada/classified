<template>
  <q-page class="q-pa-lg">
    <div class="text-h5 q-mb-md">Fichas</div>

    <div class="text-subtitle2 q-mb-sm">Alumno</div>
    <q-form class="row q-col-gutter-sm q-mb-lg" @submit.prevent="crearAlumno">
      <div class="col-3">
        <q-select v-model="alumno.tipo_doc" outlined dense :options="tiposDoc" label="Documento" />
      </div>
      <div class="col-3">
        <q-input v-model="alumno.numero_doc" outlined dense label="Número" />
      </div>
      <div class="col-3">
        <q-input v-model="alumno.nombres" outlined dense label="Nombres" />
      </div>
      <div class="col-3">
        <q-input v-model="alumno.apellidos" outlined dense label="Apellidos" />
      </div>
      <div class="col-12">
        <q-btn type="submit" color="primary" label="Registrar alumno" />
      </div>
    </q-form>

    <div class="text-subtitle2 q-mb-sm">Representante</div>
    <q-form class="row q-col-gutter-sm q-mb-lg" @submit.prevent="crearRepresentante">
      <div class="col-6">
        <q-select
          v-model="rep.alumno_id"
          outlined
          dense
          emit-value
          map-options
          :options="alumnoOptions"
          label="Alumno"
        />
      </div>
      <div class="col-3">
        <q-select v-model="rep.parentesco" outlined dense :options="parentescos" label="Parentesco" />
      </div>
      <div class="col-3">
        <q-select v-model="rep.tipo_doc" outlined dense :options="tiposDoc" label="Documento" />
      </div>
      <div class="col-3">
        <q-input v-model="rep.numero_doc" outlined dense label="Número" />
      </div>
      <div class="col-3">
        <q-input v-model="rep.nombres" outlined dense label="Nombres" />
      </div>
      <div class="col-3">
        <q-input v-model="rep.apellidos" outlined dense label="Apellidos" />
      </div>
      <div class="col-3">
        <q-input v-model="rep.email" outlined dense type="email" label="Email" />
      </div>
      <div class="col-3">
        <q-input v-model="rep.password" outlined dense type="password" label="Clave" />
      </div>
      <div class="col-12">
        <q-btn type="submit" color="secondary" label="Registrar representante" />
      </div>
    </q-form>

    <q-list bordered separator>
      <q-item v-for="p in lista" :key="p.id">
        <q-item-section>
          <q-item-label>{{ p.nombres }} {{ p.apellidos }}</q-item-label>
          <q-item-label caption>{{ p.es_alumno ? 'Alumno' : 'Representante' }} · {{ p.numero_doc }}</q-item-label>
        </q-item-section>
      </q-item>
    </q-list>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { useQuasar } from 'quasar';
import { api } from 'src/boot/axios';

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
const tiposDoc = ['cedula_v', 'cedula_e', 'pasaporte', 'partida', 'expediente'];
const parentescos = ['madre', 'padre', 'abuelo', 'tutor'];
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
