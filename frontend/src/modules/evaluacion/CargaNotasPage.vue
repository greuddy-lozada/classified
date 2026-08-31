<template>
  <q-page class="q-pa-lg">
    <div class="text-h5 q-mb-md">Carga de evaluación</div>
    <q-form class="row q-col-gutter-sm q-mb-md" @submit.prevent="cargarNota">
      <div class="col-12">
        <q-input v-model="inscripcionId" outlined dense label="ID inscripción" />
      </div>
      <div class="col-4">
        <q-input v-model="lapsoId" outlined dense label="ID lapso" />
      </div>
      <div class="col-4">
        <q-input v-model="materiaId" outlined dense label="ID materia" />
      </div>
      <div class="col-4">
        <q-input v-model.number="valor" outlined dense type="number" label="Nota 1-20" />
      </div>
      <div class="col-12">
        <q-btn type="submit" color="primary" label="Guardar nota" />
      </div>
    </q-form>
    <q-form class="row q-col-gutter-sm" @submit.prevent="cargarInforme">
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
import { ref } from 'vue';
import { useQuasar } from 'quasar';
import { api } from 'src/boot/axios';

const $q = useQuasar();
const inscripcionId = ref('');
const lapsoId = ref('');
const materiaId = ref('');
const valor = ref(10);
const area = ref('lenguaje');
const juicio = ref('en_proceso');
const comentario = ref('');
const areas = ['lenguaje', 'socioemocional', 'psicomotor', 'exploracion'];
const juicios = ['logrado', 'en_proceso', 'iniciado'];

async function cargarNota() {
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
</script>
