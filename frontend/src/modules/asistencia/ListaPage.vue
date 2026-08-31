<template>
  <q-page class="q-pa-lg">
    <div class="text-h5 q-mb-md">Asistencia</div>
    <div class="row q-col-gutter-sm q-mb-md">
      <div class="col-4">
        <q-input v-model="seccionId" outlined dense label="ID sección" />
      </div>
      <div class="col-4">
        <q-input v-model="fecha" outlined dense type="date" label="Fecha" />
      </div>
      <div class="col-4">
        <q-input v-model="materiaId" outlined dense label="ID materia (media)" />
      </div>
      <div class="col-12">
        <q-btn color="primary" label="Cargar lista" @click="cargar" />
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
import { ref } from 'vue';
import { useQuasar } from 'quasar';
import { api } from 'src/boot/axios';

interface Item {
  inscripcion_id: string;
  alumno_nombres: string;
  alumno_apellidos: string;
  estado: string | null;
}

const $q = useQuasar();
const seccionId = ref('');
const fecha = ref(new Date().toISOString().slice(0, 10));
const materiaId = ref('');
const lista = ref<Item[]>([]);
const estados = [
  { label: 'P', value: 'presente' },
  { label: 'A', value: 'ausente' },
  { label: 'J', value: 'justificado' },
  { label: 'T', value: 'tardanza' },
];

async function cargar() {
  try {
    const { data } = await api.get<Item[]>('/asistencia/lista', {
      params: {
        seccion_id: seccionId.value,
        fecha: fecha.value,
        materia_id: materiaId.value || undefined,
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
      materia_id: materiaId.value || null,
    });
    await cargar();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo marcar' });
  }
}
</script>
