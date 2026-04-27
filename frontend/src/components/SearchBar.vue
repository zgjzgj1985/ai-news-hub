<template>
  <div class="search-bar">
    <div class="search-input-wrap">
      <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input
        ref="inputRef"
        type="text"
        class="search-input"
        :placeholder="placeholder"
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
        @keyup.enter="handleSearch"
        @keyup.escape="$emit('update:modelValue', '')"
      />
      <button v-if="modelValue" class="clear-btn" @click="$emit('update:modelValue', '')" title="清除">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>
    <select v-if="showSort" class="sort-select" :value="sort" @change="$emit('update:sort', $event.target.value)">
      <option value="newest">最新优先</option>
      <option value="oldest">最早优先</option>
    </select>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '搜索标题或摘要...' },
  showSort: { type: Boolean, default: false },
  sort: { type: String, default: 'newest' },
})
const emit = defineEmits(['update:modelValue', 'update:sort', 'search'])

const inputRef = ref(null)

function handleSearch() {
  emit('search')
  inputRef.value?.blur()
}
</script>

<style scoped>
.search-bar {
  display: flex;
  gap: var(--space-3);
  align-items: center;
}

.search-input-wrap {
  position: relative;
  flex: 1;
}

.search-icon {
  position: absolute;
  left: var(--space-3);
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: var(--space-2) var(--space-4) var(--space-2) calc(var(--space-3) + 16px + var(--space-2));
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 999px;
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  outline: none;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}
.search-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-dim);
}
.search-input::placeholder {
  color: var(--text-muted);
}

.clear-btn {
  position: absolute;
  right: var(--space-3);
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  padding: 2px;
  border-radius: 50%;
  transition: color var(--transition-fast);
}
.clear-btn:hover {
  color: var(--text-primary);
}

.sort-select {
  padding: var(--space-2) var(--space-3);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  outline: none;
  cursor: pointer;
  transition: border-color var(--transition-fast);
}
.sort-select:focus {
  border-color: var(--accent);
}
.sort-select option {
  background: var(--bg-surface);
}
</style>
