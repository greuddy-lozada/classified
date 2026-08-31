<template>
  <q-layout view="hHh Lpr lFf" class="public-shell">
    <q-page-container>
      <q-page class="q-pa-lg flex flex-center">
        <div class="login-grid">
          <div class="login-panel">
            <q-btn
              flat
              no-caps
              dense
              color="dark"
              icon="arrow_back"
              label="Inicio"
              to="/"
              class="q-mb-md"
            />
            <h1 class="text-h5 q-mb-xs">Ingresar</h1>
            <p class="text-caption text-grey-8 q-mb-lg">Correo y clave de tu plantel o de plataforma.</p>
            <q-form class="q-gutter-md" @submit.prevent="handleSubmit">
              <q-input
                v-model="email"
                outlined
                type="email"
                autocomplete="username"
                label="Correo"
                lazy-rules
                :rules="[(val) => (val && val.length > 0) || 'Escribe tu correo']"
              />
              <q-input
                v-model="password"
                outlined
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                label="Contraseña"
                lazy-rules
                :rules="[(val) => (val && val.length > 0) || 'Escribe tu contraseña']"
              >
                <template #append>
                  <q-icon
                    :name="showPassword ? 'visibility_off' : 'visibility'"
                    class="cursor-pointer"
                    :aria-label="showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'"
                    @click="showPassword = !showPassword"
                  />
                </template>
              </q-input>
              <q-btn
                unelevated
                no-caps
                type="submit"
                color="primary"
                text-color="white"
                class="full-width"
                label="Entrar"
                :loading="loading"
                :disable="loading"
              />
            </q-form>
          </div>
          <div class="login-aside">
            <p class="text-caption text-uppercase hero-kicker">Classified</p>
            <h2 class="login-title font-black">Tu colegio a un clic</h2>
            <p class="login-lead">
              Dirección, secretaría, docente y representante entran al mismo sistema. Cada plantel
              queda aislado.
            </p>
          </div>
        </div>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRouter } from 'vue-router';
import { useAuthStore } from 'src/stores/auth';

const $q = useQuasar();
const router = useRouter();
const auth = useAuthStore();
const email = ref('');
const password = ref('');
const showPassword = ref(false);
const loading = ref(false);

async function handleSubmit() {
  loading.value = true;
  try {
    await auth.login(email.value, password.value);
    if (auth.me?.es_plataforma) {
      await router.push('/plataforma');
      return;
    }
    if (!auth.me?.organizacion_id || !auth.me?.rol) {
      await router.push('/seleccionar');
      return;
    }
    await router.push('/dashboard');
  } catch {
    $q.notify({ type: 'negative', message: 'Correo o contraseña incorrectos', position: 'top' });
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-grid {
  width: min(960px, 100%);
  display: grid;
  gap: 2rem;
  align-items: center;
}

@media (min-width: 768px) {
  .login-grid {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1.1fr);
  }
}

.login-panel {
  background: var(--color-surface);
  color: var(--color-fg);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 1.5rem 1.5rem 1.75rem;
}

.hero-kicker {
  letter-spacing: 0.12em;
  color: var(--color-primary);
}

.login-title {
  font-size: clamp(1.8rem, 4vw, 2.6rem);
  line-height: 1.15;
  margin: 0 0 0.75rem;
}

.login-lead {
  margin: 0;
  line-height: 1.55;
  color: var(--color-muted);
}

:deep(.q-btn) {
  min-height: 44px;
}

:deep(.q-btn:focus-visible) {
  outline: 3px solid var(--color-primary);
  outline-offset: 3px;
}
</style>
