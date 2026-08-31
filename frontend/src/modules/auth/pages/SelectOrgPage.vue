<template>
  <q-page class="q-pa-lg">
    <q-card class="q-pa-md" style="max-width: 420px; margin: 4rem auto">
      <div class="text-h6 q-mb-md">Elige plantel</div>
      <q-list separator>
        <q-item
          v-for="m in auth.membresias"
          :key="m.organizacion_id + m.rol"
          clickable
          @click="pick(m)"
        >
          <q-item-section>
            <q-item-label>{{ m.organizacion_nombre }}</q-item-label>
            <q-item-label caption>{{ m.rol }}</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useAuthStore, type Membresia } from 'src/stores/auth';

const auth = useAuthStore();
const router = useRouter();

async function pick(m: Membresia) {
  await auth.seleccionar(m.organizacion_id, m.rol);
  await router.push('/dashboard');
}
</script>
