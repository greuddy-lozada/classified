<template>
  <AppPage title="Cobro" subtitle="Genera matrícula y mensualidades. Marca pagada o morosa.">
    <div class="app-card">
      <div class="row q-col-gutter-md">
        <div class="col-12 col-sm-6">
          <q-select v-model="anioId" outlined emit-value map-options :options="anioOptions" label="Año escolar" />
        </div>
        <div class="col-12 col-sm-6">
          <q-select
            v-model="periodos"
            outlined
            multiple
            emit-value
            map-options
            :options="mesOptions"
            label="Mensualidades"
          />
        </div>
        <div class="col-12">
          <q-btn unelevated color="primary" no-caps label="Generar cargos" class="q-mr-sm" @click="generar" />
          <q-btn outline no-caps color="primary" label="Actualizar" @click="cargar" />
        </div>
      </div>
    </div>
    <div class="app-card">
      <p v-if="!lista.length" class="app-empty">No hay cargos. Genera matrícula y los meses del año.</p>
      <q-list v-else separator>
        <q-item v-for="c in lista" :key="c.id" class="q-py-md">
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
              :options="estados"
              @update:model-value="(v) => marcar(c.id, v)"
            />
          </q-item-section>
        </q-item>
      </q-list>
    </div>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useQuasar } from 'quasar';
import { api } from 'src/boot/axios';
import AppPage from '../dashboard/AppPage.vue';

interface Anio {
  id: string;
  nombre: string;
}
interface Cargo {
  id: string;
  alumno_nombres: string;
  alumno_apellidos: string;
  concepto: string;
  estado: string;
  nota: string | null;
}

const MESES = [
  [9, 'Septiembre'],
  [10, 'Octubre'],
  [11, 'Noviembre'],
  [12, 'Diciembre'],
  [1, 'Enero'],
  [2, 'Febrero'],
  [3, 'Marzo'],
  [4, 'Abril'],
  [5, 'Mayo'],
  [6, 'Junio'],
  [7, 'Julio'],
] as const;

const $q = useQuasar();
const anios = ref<Anio[]>([]);
const anioId = ref<string | null>(null);
const periodos = ref<string[]>([]);
const lista = ref<Cargo[]>([]);
const estados = [
  { label: 'Pendiente', value: 'pendiente' },
  { label: 'Pagada', value: 'pagada' },
  { label: 'Morosa', value: 'morosa' },
];

const anioOptions = computed(() => anios.value.map((a) => ({ label: a.nombre, value: a.id })));
const anioActual = computed(() => anios.value.find((a) => a.id === anioId.value));
const mesOptions = computed(() => {
  const nombre = anioActual.value?.nombre ?? '';
  const match = /^(\d{4})-(\d{4})$/.exec(nombre);
  const inicio = match ? Number(match[1]) : new Date().getFullYear();
  const fin = match ? Number(match[2]) : inicio + 1;
  return MESES.map(([mes, label]) => {
    const year = mes >= 9 ? inicio : fin;
    const value = `${year}-${String(mes).padStart(2, '0')}`;
    return { label: `${label} ${year}`, value };
  });
});

async function cargarAnios() {
  const { data } = await api.get<Anio[]>('/periodo/anios');
  anios.value = data;
  if (!anioId.value && data[0]) anioId.value = data[0].id;
}

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
    await api.post('/cobro/generar', { anio_escolar_id: anioId.value, periodos: periodos.value });
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

watch(anioId, () => {
  periodos.value = mesOptions.value.map((m) => m.value);
  void cargar();
});
void cargarAnios();
</script>
