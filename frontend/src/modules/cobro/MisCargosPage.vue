<template>
  <q-page class="q-pa-lg">
    <div class="text-h5 q-mb-md">Matrícula y mensualidades</div>
    <q-list bordered separator>
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
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { api } from 'src/boot/axios';

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
