<template>
  <AppPage title="Inscripción" subtitle="Estado de cupo, recaudos y matrícula de tus pupilos.">
    <div class="app-card">
      <p v-if="!lista.length" class="app-empty">No hay inscripciones para mostrar.</p>
      <q-list v-else separator>
        <q-item v-for="ins in lista" :key="ins.id">
          <q-item-section>
            <q-item-label>{{ ins.alumno_nombres }} {{ ins.alumno_apellidos }}</q-item-label>
            <q-item-label caption>
              {{ ins.estado }} · matrícula {{ ins.estado_matricula }}
              · {{ ins.recaudos_pendientes ? 'faltan recaudos' : 'recaudos al día' }}
            </q-item-label>
          </q-item-section>
          <q-item-section side>
            <q-btn unelevated no-caps color="primary" text-color="dark" label="Boletín" :to="`/dashboard/boletines/${ins.id}`" />
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

interface Inscripcion {
  id: string;
  alumno_nombres: string;
  alumno_apellidos: string;
  estado: string;
  estado_matricula: string;
  recaudos_pendientes: boolean;
}

const lista = ref<Inscripcion[]>([]);

onMounted(async () => {
  const { data } = await api.get<Inscripcion[]>('/inscripciones/mias');
  lista.value = data;
});
</script>
