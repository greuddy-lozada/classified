<template>
  <AppPage title="Boletín" :subtitle="boletin ? `${boletin.alumno_nombres} ${boletin.alumno_apellidos}` : 'Cargando…'">
    <div class="app-card" v-if="boletin">
      <div class="row items-center q-mb-md">
        <div class="col text-caption">
          {{ boletin.esquema === 'informe' ? 'Informe descriptivo' : 'Calificaciones' }}
          <span v-if="boletin.promedio_final != null"> · final {{ boletin.promedio_final }}</span>
          <q-badge v-if="boletin.necesita_reparacion" color="negative" label="reparación" class="q-ml-sm" />
        </div>
        <q-btn unelevated no-caps color="primary" text-color="dark" label="Descargar PDF" @click="descargar" />
      </div>
      <div v-for="lapso in boletin.lapsos" :key="lapso.lapso_id" class="q-mb-md">
        <div class="text-subtitle2 text-weight-bold">
          {{ lapso.lapso_nombre }}
          <q-badge v-if="lapso.cerrado" color="grey" text-color="dark" label="cerrado" class="q-ml-sm" />
          <span v-if="lapso.promedio != null" class="text-caption"> · promedio {{ lapso.promedio }}</span>
        </div>
        <q-list separator>
          <q-item v-for="n in lapso.notas" :key="n.materia_id">
            <q-item-section>{{ n.materia_nombre }}</q-item-section>
            <q-item-section side>{{ n.valor }}</q-item-section>
          </q-item>
          <q-item v-for="i in lapso.informes" :key="i.area">
            <q-item-section>{{ i.area }} · {{ i.juicio }}</q-item-section>
            <q-item-section side caption>{{ i.comentario }}</q-item-section>
          </q-item>
        </q-list>
      </div>
    </div>
  </AppPage>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { api } from 'src/boot/axios';
import AppPage from '../dashboard/AppPage.vue';

interface Boletin {
  alumno_nombres: string;
  alumno_apellidos: string;
  esquema: string;
  promedio_final: number | null;
  necesita_reparacion: boolean;
  lapsos: {
    lapso_id: string;
    lapso_nombre: string;
    cerrado: boolean;
    promedio: number | null;
    notas: { materia_id: string; materia_nombre: string; valor: number }[];
    informes: { area: string; juicio: string; comentario: string }[];
  }[];
}

const route = useRoute();
const boletin = ref<Boletin | null>(null);

onMounted(async () => {
  const id = String(route.params.inscripcionId);
  const { data } = await api.get<Boletin>(`/evaluacion/boletines/${id}`);
  boletin.value = data;
});

async function descargar() {
  const id = String(route.params.inscripcionId);
  const { data } = await api.get<Blob>(`/evaluacion/boletines/${id}/pdf`, { responseType: 'blob' });
  const url = URL.createObjectURL(data);
  const a = document.createElement('a');
  a.href = url;
  a.download = boletin.value?.esquema === 'informe' ? 'informe.pdf' : 'boletin.pdf';
  a.click();
  URL.revokeObjectURL(url);
}
</script>
