<template>
  <q-page class="q-pa-lg">
    <div class="text-h5 q-mb-md">Cobro</div>
    <div class="row q-col-gutter-sm q-mb-md">
      <div class="col-6">
        <q-input v-model="anioId" outlined dense label="ID año escolar" />
      </div>
      <div class="col-6">
        <q-input v-model="periodos" outlined dense label="Meses (2026-09,2026-10)" />
      </div>
      <div class="col-12">
        <q-btn color="primary" label="Generar cargos" class="q-mr-sm" @click="generar" />
        <q-btn outline color="primary" label="Cargar" @click="cargar" />
      </div>
    </div>
    <q-list bordered separator>
      <q-item v-for="c in lista" :key="c.id">
        <q-item-section>
          <q-item-label>{{ c.alumno_nombres }} {{ c.alumno_apellidos }}</q-item-label>
          <q-item-label caption>
            {{ c.concepto }} · {{ c.estado }}
            <span v-if="c.nota"> · {{ c.nota }}</span>
          </q-item-label>
        </q-item-section>
        <q-item-section side>
          <q-btn-toggle
            :model-value="c.estado"
            unelevated
            dense
            :options="estados"
            @update:model-value="(v) => marcar(c.id, v)"
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

interface Cargo {
  id: string;
  alumno_nombres: string;
  alumno_apellidos: string;
  concepto: string;
  estado: string;
  nota: string | null;
}

const $q = useQuasar();
const anioId = ref('');
const periodos = ref('2026-09,2026-10,2026-11');
const lista = ref<Cargo[]>([]);
const estados = [
  { label: 'Pendiente', value: 'pendiente' },
  { label: 'Pagada', value: 'pagada' },
  { label: 'Morosa', value: 'morosa' },
];

async function cargar() {
  try {
    const { data } = await api.get<Cargo[]>('/cobro', {
      params: { anio_escolar_id: anioId.value || undefined },
    });
    lista.value = data;
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudieron cargar los cargos' });
  }
}

async function generar() {
  if (!anioId.value) return;
  try {
    await api.post('/cobro/generar', {
      anio_escolar_id: anioId.value,
      periodos: periodos.value
        .split(',')
        .map((p) => p.trim())
        .filter(Boolean),
    });
    await cargar();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudieron generar los cargos' });
  }
}

async function marcar(id: string, estado: string) {
  try {
    await api.patch(`/cobro/${id}`, { estado, nota: estado === 'pagada' ? 'efectivo' : null });
    await cargar();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo marcar el cargo' });
  }
}
</script>
