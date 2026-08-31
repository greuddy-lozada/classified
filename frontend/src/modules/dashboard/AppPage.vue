<template>
  <q-page class="app-page">
    <header class="app-page__head">
      <h1 class="app-page__title">{{ title }}</h1>
      <p v-if="subtitle" class="app-page__sub">{{ subtitle }}</p>
    </header>
    <slot />
  </q-page>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  subtitle?: string;
}>();
</script>
