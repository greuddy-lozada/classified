<template>
  <q-page class="q-pa-lg">
    <div class="text-h5">{{ greeting }}</div>
    <div class="text-caption q-mb-md">{{ auth.me?.email }} · {{ auth.me?.rol ?? 'plataforma' }}</div>
    <q-list v-if="pupilos.length" bordered separator>
      <q-item v-for="p in pupilos" :key="p.id">
        <q-item-section>
          <q-item-label>{{ p.alumno_nombres }} {{ p.alumno_apellidos }}</q-item-label>
          <q-item-label caption>{{ p.estado }} · matrícula {{ p.estado_matricula }}</q-item-label>
        </q-item-section>
        <q-item-section side>
          <q-btn dense flat label="Boletín" :to="`/dashboard/boletines/${p.id}`" />
        </q-item-section>
      </q-item>
    </q-list>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useAuthStore } from 'src/stores/auth';
import { api } from 'src/boot/axios';

interface Pupilo {
  id: string;
  alumno_nombres: string;
  alumno_apellidos: string;
  estado: string;
  estado_matricula: string;
}

const auth = useAuthStore();
const pupilos = ref<Pupilo[]>([]);
const greeting = computed(() => {
  if (auth.me?.es_plataforma && !auth.me.rol) return 'Plataforma';
  if (auth.me?.rol === 'representante') return 'Tus pupilos';
  return 'Plantel';
});

onMounted(async () => {
  if (auth.me?.rol !== 'representante') return;
  const { data } = await api.get<Pupilo[]>('/inscripciones/mias');
  pupilos.value = data;
});
</script>
