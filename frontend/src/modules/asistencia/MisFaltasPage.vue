<template>
  <q-page class="q-pa-lg">
    <div class="text-h5 q-mb-md">Asistencia de tus pupilos</div>
    <q-list bordered separator>
      <q-item v-for="r in lista" :key="r.inscripcion_id">
        <q-item-section>
          <q-item-label>{{ r.alumno_nombres }} {{ r.alumno_apellidos }}</q-item-label>
          <q-item-label caption>
            {{ r.porcentaje ?? '—' }}% · {{ r.ausentes }} ausencias
          </q-item-label>
        </q-item-section>
      </q-item>
    </q-list>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { api } from 'src/boot/axios';

interface Resumen {
  inscripcion_id: string;
  alumno_nombres: string;
  alumno_apellidos: string;
  porcentaje: number | null;
  ausentes: number;
}

const lista = ref<Resumen[]>([]);

onMounted(async () => {
  const { data } = await api.get<Resumen[]>('/asistencia/mias');
  lista.value = data;
});
</script>
