<template>
  <div class="tag-filter">
    <button
      v-for="item in items"
      :key="item.value"
      class="filter-btn"
      :class="{ active: modelValue === item.value }"
      @click="handleClick(item.value)"
    >
      {{ item.label }}
      <span v-if="item.count > 0" class="filter-count">{{ item.count }}</span>
    </button>
  </div>
</template>

<script setup>
const props = defineProps({
  modelValue: { type: String, default: '' },
  items: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue', 'tagClick'])

function handleClick(value) {
  emit('update:modelValue', value)
  emit('tagClick', value)
}
</script>

<style scoped>
.tag-filter {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.filter-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 999px;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-base);
  white-space: nowrap;
}
.filter-btn:hover {
  border-color: var(--text-muted);
  color: var(--text-primary);
  background: var(--bg-elevated);
}
.filter-btn.active {
  background: var(--accent-dim);
  border-color: var(--accent);
  color: var(--accent);
}

.filter-count {
  font-size: var(--font-size-xs);
  background: var(--bg-elevated);
  color: var(--text-muted);
  padding: 1px 6px;
  border-radius: 999px;
  min-width: 20px;
  text-align: center;
}
.filter-btn.active .filter-count {
  background: rgba(57, 208, 216, 0.2);
  color: var(--accent);
}
</style>
