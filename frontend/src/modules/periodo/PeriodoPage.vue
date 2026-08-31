<template>
  <q-page class="q-pa-lg">
    <div class="text-h5 q-mb-md">Año escolar</div>

    <q-form class="row q-col-gutter-sm q-mb-lg" @submit.prevent="crearAnio">
      <div class="col-8">
        <q-input v-model="nuevoAnio" outlined dense label="Nombre (ej. 2026-2027)" />
      </div>
      <div class="col-4">
        <q-btn type="submit" color="primary" label="Crear año" class="full-width" />
      </div>
    </q-form>

    <div v-for="anio in anios" :key="anio.id" class="q-mb-lg">
      <div class="text-subtitle1">
        {{ anio.nombre }} <q-badge v-if="anio.activo" color="positive" label="activo" />
      </div>
      <div class="row q-col-gutter-sm q-mb-sm">
        <div v-for="l in anio.lapsos" :key="l.id" class="col-auto">
          <q-btn
            dense
            unelevated
            :color="l.cerrado ? 'grey' : 'secondary'"
            :label="l.cerrado ? `${l.nombre} · reabrir` : `${l.nombre} · cerrar`"
            @click="l.cerrado ? reabrirLapso(l.id) : cerrarLapso(l.id)"
          />
        </div>
      </div>

      <q-form class="row q-col-gutter-sm q-mb-sm" @submit.prevent="crearGrado(anio.id)">
        <div class="col-3">
          <q-select v-model="formGrado.nivel" outlined dense :options="niveles" label="Nivel" />
        </div>
        <div class="col-4">
          <q-input v-model="formGrado.nombre" outlined dense label="Grado (4°, 3er año)" />
        </div>
        <div class="col-3">
          <q-select v-model="formGrado.esquema" outlined dense :options="esquemas" label="Esquema" clearable />
        </div>
        <div class="col-2">
          <q-btn type="submit" color="secondary" label="Grado" class="full-width" />
        </div>
      </q-form>

      <q-list bordered separator>
        <q-item v-for="g in gradosPorAnio[anio.id] ?? []" :key="g.id">
          <q-item-section>
            <q-item-label>{{ g.nivel }} · {{ g.nombre }}</q-item-label>
            <q-item-label caption>
              {{ g.esquema_evaluacion }} ·
              {{ g.secciones.map((s) => s.letra + ' ' + s.turno).join(', ') || 'sin sección' }}
            </q-item-label>
          </q-item-section>
          <q-item-section side>
            <q-btn dense flat label="+ A mañana" @click="crearSeccion(g.id, 'A', 'manana')" />
          </q-item-section>
        </q-item>
      </q-list>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import { useQuasar } from 'quasar';
import { api } from 'src/boot/axios';

interface Lapso {
  id: string;
  numero: number;
  nombre: string;
  cerrado: boolean;
}
interface Seccion {
  id: string;
  letra: string;
  turno: string;
}
interface Grado {
  id: string;
  nivel: string;
  nombre: string;
  esquema_evaluacion: string;
  secciones: Seccion[];
}
interface Anio {
  id: string;
  nombre: string;
  activo: boolean;
  lapsos: Lapso[];
}

const $q = useQuasar();
const anios = ref<Anio[]>([]);
const gradosPorAnio = ref<Record<string, Grado[]>>({});
const nuevoAnio = ref('2026-2027');
const niveles = ['inicial', 'primaria', 'media'];
const esquemas = ['informe', 'numerico'];
const formGrado = reactive({ nivel: 'primaria', nombre: '', esquema: null as string | null });

async function cargar() {
  const { data } = await api.get<Anio[]>('/periodo/anios');
  anios.value = data;
  for (const anio of data) {
    const res = await api.get<Grado[]>('/periodo/grados', { params: { anio_escolar_id: anio.id } });
    gradosPorAnio.value[anio.id] = res.data;
  }
}

async function crearAnio() {
  try {
    await api.post('/periodo/anios', { nombre: nuevoAnio.value });
    await cargar();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo crear el año' });
  }
}

async function crearGrado(anioId: string) {
  try {
    const payload: Record<string, unknown> = {
      anio_escolar_id: anioId,
      nivel: formGrado.nivel,
      nombre: formGrado.nombre,
    };
    if (formGrado.esquema) payload.esquema_evaluacion = formGrado.esquema;
    await api.post('/periodo/grados', payload);
    formGrado.nombre = '';
    await cargar();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo crear el grado' });
  }
}

async function crearSeccion(gradoId: string, letra: string, turno: string) {
  try {
    await api.post('/periodo/secciones', { grado_id: gradoId, letra, turno });
    await cargar();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo crear la sección' });
  }
}

async function cerrarLapso(id: string) {
  try {
    await api.post(`/periodo/lapsos/${id}/cerrar`);
    await cargar();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo cerrar el lapso' });
  }
}

async function reabrirLapso(id: string) {
  try {
    await api.post(`/periodo/lapsos/${id}/reabrir`);
    await cargar();
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo reabrir el lapso' });
  }
}

onMounted(cargar);
</script>
