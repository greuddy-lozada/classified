<template>
  <q-page class="q-pa-lg">
    <div class="text-h5">{{ greeting }}</div>
    <div class="text-caption">{{ auth.me?.email }} · {{ auth.me?.rol ?? 'plataforma' }}</div>
  </q-page>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useAuthStore } from 'src/stores/auth';

const auth = useAuthStore();
const greeting = computed(() => {
  if (auth.me?.es_plataforma && !auth.me.rol) return 'Plataforma';
  if (auth.me?.rol === 'representante') return 'Tus pupilos';
  return 'Plantel';
});
</script>
