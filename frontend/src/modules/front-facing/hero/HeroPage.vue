<template>
  <q-layout view="hHh Lpr lFf" class="public-shell">
    <q-header class="hero-bar">
      <q-toolbar class="q-px-lg">
        <q-toolbar-title class="text-weight-bold">Classified</q-toolbar-title>
        <q-btn
          unelevated
          no-caps
          color="primary"
          text-color="white"
          label="Ingresar"
          to="/login"
          padding="sm lg"
        />
      </q-toolbar>
    </q-header>

    <q-page-container>
      <q-page class="q-pa-lg flex flex-center">
        <div class="hero-copy">
          <p class="text-caption text-uppercase hero-kicker">SIS para colegios privados</p>
          <h1 class="hero-title font-black">
            El expediente del colegio,<br />
            en un solo lugar.
          </h1>
          <p class="hero-lead">
            Inscripciones, asistencia, notas e informe, y estado de matrícula y mensualidad.
            Un plantel no ve el de al lado.
          </p>
          <q-btn
            unelevated
            no-caps
            size="lg"
            color="primary"
            text-color="white"
            class="q-mb-xl"
            label="Ingresar al plantel"
            to="/login"
            padding="md xl"
          />
          <div class="row q-col-gutter-md">
            <div v-for="item in bloques" :key="item.title" class="col-12 col-sm-6">
              <div class="hero-card">
                <div class="text-subtitle2 text-weight-bold">{{ item.title }}</div>
                <div class="text-caption">{{ item.caption }}</div>
              </div>
            </div>
          </div>
        </div>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
const bloques = [
  { title: 'Plantel', caption: 'Año, secciones, fichas y cupo.' },
  { title: 'Docente', caption: 'Lista del día y carga de notas.' },
  { title: 'Representante', caption: 'Boletín, faltas y cobro.' },
  { title: 'Plataforma', caption: 'Alta de colegios, cada uno aislado.' },
];
</script>

<style scoped>
.hero-bar {
  background: var(--color-surface);
  color: var(--color-fg);
  box-shadow: none;
  border-bottom: 1px solid var(--color-border);
}

.hero-copy {
  max-width: 40rem;
}

.hero-kicker {
  letter-spacing: 0.12em;
  color: var(--color-primary);
}

.hero-title {
  font-size: clamp(2rem, 6vw, 3.4rem);
  line-height: 1.15;
  margin: 0 0 1rem;
}

.hero-lead {
  font-size: 1.1rem;
  line-height: 1.55;
  color: var(--color-muted);
  margin: 0 0 1.75rem;
}

.hero-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 1rem 1.1rem;
  min-height: 5.5rem;
}

:deep(.q-btn) {
  min-height: 44px;
  transition: transform 180ms ease, filter 180ms ease;
}

:deep(.q-btn:hover) {
  filter: brightness(1.06);
}

:deep(.q-btn:focus-visible) {
  outline: 3px solid var(--color-primary);
  outline-offset: 3px;
}
</style>
