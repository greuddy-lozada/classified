<template>
  <q-page class="q-pa-lg">
    <div class="text-h5 q-mb-md">Alta de planteles</div>
    <q-form class="row q-col-gutter-sm q-mb-lg" @submit.prevent="crear">
      <div class="col-6">
        <q-input v-model="form.nombre" outlined dense label="Nombre del colegio" />
      </div>
      <div class="col-6">
        <q-input v-model="form.rif" outlined dense label="RIF" />
      </div>
      <div class="col-4">
        <q-input v-model="form.admin_nombres" outlined dense label="Admin nombres" />
      </div>
      <div class="col-4">
        <q-input v-model="form.admin_apellidos" outlined dense label="Admin apellidos" />
      </div>
      <div class="col-4">
        <q-input v-model="form.admin_email" outlined dense type="email" label="Admin email" />
      </div>
      <div class="col-4">
        <q-input v-model="form.admin_password" outlined dense type="password" label="Admin clave" />
      </div>
      <div class="col-8">
        <q-btn type="submit" color="primary" label="Crear plantel" />
      </div>
    </q-form>
    <q-list bordered separator>
      <q-item v-for="o in lista" :key="o.id">
        <q-item-section>
          <q-item-label>{{ o.nombre }}</q-item-label>
          <q-item-label caption>{{ o.rif || 'sin RIF' }}</q-item-label>
        </q-item-section>
      </q-item>
    </q-list>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import { useQuasar } from 'quasar';
import { api } from 'src/boot/axios';

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
