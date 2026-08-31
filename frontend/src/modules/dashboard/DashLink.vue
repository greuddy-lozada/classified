<template>
  <q-item
    clickable
    class="app-link"
    :class="{ 'app-link--active': isActive }"
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
import { computed, defineComponent } from 'vue';
import { useRoute } from 'vue-router';

export interface DashLinkProps {
  title: string;
  caption?: string;
  link?: string;
  icon?: string;
  exact?: boolean;
}

export default defineComponent({
  name: 'DashLink',
  props: {
    title: { type: String, required: true },
    caption: { type: String, default: '' },
    link: { type: String, default: '#' },
    icon: { type: String, default: '' },
    exact: { type: Boolean, default: false },
  },
  setup(props) {
    const route = useRoute();
    const isActive = computed(() => {
      if (!props.link.startsWith('/')) return false;
      if (props.exact) return route.path === props.link;
      return route.path === props.link || route.path.startsWith(`${props.link}/`);
    });
    return { isActive };
  },
});
</script>

<style scoped>
.app-link {
  color: var(--color-fg);
  min-height: 48px;
  border-radius: 8px;
  margin: 0 0.5rem;
}

.app-link :deep(.q-item__label--caption) {
  color: var(--color-muted);
}

.app-link--active {
  background: rgba(15, 107, 76, 0.1);
  color: var(--color-primary);
}
</style>
