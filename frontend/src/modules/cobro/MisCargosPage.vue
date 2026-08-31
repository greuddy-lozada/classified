<template>
  <AppPage title="Cobro" subtitle="Matrícula y mensualidades de tus pupilos.">
    <div class="app-card">
      <p v-if="!lista.length" class="app-empty">No hay cargos cargados todavía.</p>
      <q-list v-else separator>
        <q-item v-for="c in lista" :key="c.id">
          <q-item-section>
            <q-item-label>{{ c.alumno_nombres }} {{ c.alumno_apellidos }}</q-item-label>
            <q-item-label caption>
              {{ c.concepto }} · {{ c.estado }}
              <span v-if="c.nota"> · {{ c.nota }}</span>
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

interface Cargo {
  id: string;
  alumno_nombres: string;
  alumno_apellidos: string;
  concepto: string;
  estado: string;
  nota: string | null;
}

const lista = ref<Cargo[]>([]);

onMounted(async () => {
  const { data } = await api.get<Cargo[]>('/cobro/mios');
  lista.value = data;
});
</script>
