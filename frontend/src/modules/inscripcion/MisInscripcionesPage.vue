<template>
  <q-page class="q-pa-lg">
    <div class="text-h5 q-mb-md">Inscripción de tus pupilos</div>
    <q-list bordered separator>
      <q-item v-for="ins in lista" :key="ins.id">
        <q-item-section>
          <q-item-label>{{ ins.alumno_nombres }} {{ ins.alumno_apellidos }}</q-item-label>
          <q-item-label caption>
            {{ ins.estado }} · matrícula {{ ins.estado_matricula }}
            · {{ ins.recaudos_pendientes ? 'faltan recaudos' : 'recaudos al día' }}
          </q-item-label>
        </q-item-section>
        <q-item-section side>
          <q-btn dense flat label="Boletín" :to="`/dashboard/boletines/${ins.id}`" />
        </q-item-section>
      </q-item>
    </q-list>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { api } from 'src/boot/axios';

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
