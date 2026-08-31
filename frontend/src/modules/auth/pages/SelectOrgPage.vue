<template>
  <q-layout view="hHh Lpr lFf" class="public-shell">
    <q-page-container>
      <q-page class="q-pa-lg flex flex-center">
        <div class="select-card">
          <h1 class="text-h5 q-mb-sm">Elige plantel</h1>
          <p class="text-caption text-grey-8 q-mb-md">Tu usuario tiene más de un rol o colegio.</p>
          <q-list separator>
            <q-item v-for="m in auth.membresias" :key="m.organizacion_id + m.rol" clickable @click="pick(m)">
              <q-item-section>
                <q-item-label>{{ m.organizacion_nombre }}</q-item-label>
                <q-item-label caption>{{ etiquetaRol(m.rol) }}</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </div>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useAuthStore, type Membresia } from 'src/stores/auth';

const auth = useAuthStore();
const router = useRouter();

function etiquetaRol(rol: string) {
  const map: Record<string, string> = {
    direccion: 'Dirección',
    secretaria: 'Secretaría',
    docente: 'Docente',
    representante: 'Representante',
  };
  return map[rol] ?? rol;
}

async function pick(m: Membresia) {
  await auth.seleccionar(m.organizacion_id, m.rol);
  await router.push('/dashboard');
}
</script>

<style scoped>
.select-card {
  width: min(420px, 100%);
  background: var(--color-surface);
  color: var(--color-fg);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 1.5rem;
}
</style>
