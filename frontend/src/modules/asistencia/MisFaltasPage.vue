<template>
  <AppPage title="Asistencia" subtitle="Porcentaje y ausencias de tus pupilos.">
    <div class="app-card">
      <p v-if="!lista.length" class="app-empty">Aún no hay marcas de asistencia.</p>
      <q-list v-else separator>
        <q-item v-for="r in lista" :key="r.inscripcion_id">
          <q-item-section>
            <q-item-label>{{ r.alumno_nombres }} {{ r.alumno_apellidos }}</q-item-label>
            <q-item-label caption>
              {{ r.porcentaje ?? '—' }}% de asistencia · {{ r.ausentes }} ausencias
            </q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </div>
  </AppPage>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { api } from 'src/boot/axios';
import AppPage from '../dashboard/AppPage.vue';

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
