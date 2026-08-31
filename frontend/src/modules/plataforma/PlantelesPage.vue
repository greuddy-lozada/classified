<template>
  <AppPage title="Planteles" subtitle="Crea el colegio y el primer usuario de dirección.">
    <div class="app-card">
      <h2 class="app-card__title">Nuevo plantel</h2>
      <q-form class="row q-col-gutter-md" @submit.prevent="crear">
        <div class="col-12 col-sm-6">
          <q-input v-model="form.nombre" outlined label="Nombre del colegio" />
        </div>
        <div class="col-12 col-sm-6">
          <q-input v-model="form.rif" outlined label="RIF" />
        </div>
        <div class="col-12 col-sm-6">
          <q-input v-model="form.admin_nombres" outlined label="Nombres del admin" />
        </div>
        <div class="col-12 col-sm-6">
          <q-input v-model="form.admin_apellidos" outlined label="Apellidos del admin" />
        </div>
        <div class="col-12 col-sm-6">
          <q-input v-model="form.admin_email" outlined type="email" label="Correo del admin" />
        </div>
        <div class="col-12 col-sm-6">
          <q-input v-model="form.admin_password" outlined type="password" label="Clave del admin" />
        </div>
        <div class="col-12">
          <q-btn unelevated type="submit" color="primary" text-color="dark" no-caps label="Crear plantel" />
        </div>
      </q-form>
    </div>
    <div class="app-card">
      <h2 class="app-card__title">Colegios</h2>
      <p v-if="!lista.length" class="app-empty">Aún no hay planteles.</p>
      <q-list v-else separator>
        <q-item v-for="o in lista" :key="o.id">
          <q-item-section>
            <q-item-label>{{ o.nombre }}</q-item-label>
            <q-item-label caption>{{ o.rif || 'Sin RIF' }}</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </div>
  </AppPage>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import { useQuasar } from 'quasar';
import { api } from 'src/boot/axios';
import AppPage from '../dashboard/AppPage.vue';

interface Org {
  id: string;
  nombre: string;
  rif: string | null;
}

const $q = useQuasar();
const lista = ref<Org[]>([]);
const form = reactive({
  nombre: '',
  rif: '',
  admin_nombres: '',
  admin_apellidos: '',
  admin_email: '',
  admin_password: 'clave123',
});

async function cargar() {
  const { data } = await api.get<Org[]>('/plataforma/organizaciones');
  lista.value = data;
}

async function crear() {
  try {
    await api.post('/plataforma/organizaciones', { ...form, rif: form.rif || null });
    form.nombre = '';
    form.rif = '';
    form.admin_nombres = '';
    form.admin_apellidos = '';
    form.admin_email = '';
    await cargar();
    $q.notify({ type: 'positive', message: 'Plantel creado. El admin ya puede entrar.' });
  } catch {
    $q.notify({ type: 'negative', message: 'No se pudo crear el plantel' });
  }
}

onMounted(cargar);
</script>
