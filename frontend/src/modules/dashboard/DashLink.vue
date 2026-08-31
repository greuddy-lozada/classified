<template>
  <q-item
    clickable
    :tag="link.startsWith('/') ? 'router-link' : 'a'"
    :to="link.startsWith('/') ? link : undefined"
    :href="link.startsWith('/') ? undefined : link"
    :target="link.startsWith('/') ? undefined : '_blank'"
  >
    <q-item-section v-if="icon" avatar>
      <q-icon :name="icon" />
    </q-item-section>

    <q-item-section>
      <q-item-label>{{ title }}</q-item-label>
      <q-item-label caption>{{ caption }}</q-item-label>
    </q-item-section>
  </q-item>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export interface DashLinkProps {
  title: string;
  caption?: string;
  link?: string;
  icon?: string;
}

export default defineComponent({
  name: 'DashLink',
  props: {
    title: {
      type: String,
      required: true,
    },

    caption: {
      type: String,
      default: '',
    },

    link: {
      type: String,
      default: '#',
    },

    icon: {
      type: String,
      default: '',
    },
  },
});
</script>
