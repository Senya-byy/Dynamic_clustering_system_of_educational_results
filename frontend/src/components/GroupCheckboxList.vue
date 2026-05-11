<template>
  <div class="gcl">
    <div v-if="selectedRows.length" class="gcl-summary" aria-live="polite">
      <span class="gcl-summary-label">Выбрано ({{ selectedRows.length }})</span>
      <span v-for="s in selectedRows" :key="s.id" class="gcl-chip">{{ s.name }}</span>
    </div>
    <p v-else class="gcl-empty">{{ emptyHint }}</p>

    <ul class="gcl-list" role="list">
      <li v-for="opt in options" :key="opt.id" class="gcl-item">
        <label class="gcl-label" :class="{ 'gcl-label--on': isOn(opt.id) }">
          <input
            type="checkbox"
            class="gcl-check"
            :checked="isOn(opt.id)"
            @change="toggle(opt.id, $event.target.checked)"
          />
          <span class="gcl-name">{{ opt.name }}</span>
        </label>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** { id: number, name: string } */
  options: { type: Array, required: true },
  /** Выбранные id */
  modelValue: { type: Array, default: () => [] },
  emptyHint: {
    type: String,
    default: 'Ничего не выбрано — отметьте группы ниже.',
  },
})

const emit = defineEmits(['update:modelValue'])

const idSet = computed(() => new Set((props.modelValue || []).map((x) => Number(x))))

const isOn = (id) => idSet.value.has(Number(id))

const selectedRows = computed(() => {
  const s = idSet.value
  return props.options.filter((o) => s.has(Number(o.id)))
})

const toggle = (id, on) => {
  const n = Number(id)
  const next = new Set(idSet.value)
  if (on) next.add(n)
  else next.delete(n)
  emit('update:modelValue', Array.from(next))
}
</script>

<style scoped>
.gcl {
  margin-top: 0.25rem;
}
.gcl-summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.75rem;
  padding: 0.55rem 0.65rem;
  border-radius: 10px;
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.2);
}
.gcl-summary-label {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-muted);
  margin-right: 0.15rem;
}
.gcl-chip {
  font-size: 0.82rem;
  font-weight: 600;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  background: var(--accent, #6366f1);
  color: #fff;
}
.gcl-empty {
  margin: 0 0 0.65rem;
  font-size: 0.88rem;
  color: var(--text-muted);
}
.gcl-list {
  list-style: none;
  margin: 0;
  padding: 0;
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  max-height: 280px;
  overflow-y: auto;
}
.gcl-item + .gcl-item {
  border-top: 1px solid var(--border);
}
.gcl-label {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  cursor: pointer;
  padding: 0.55rem 0.75rem;
  margin: 0;
  transition: background 0.12s;
}
.gcl-label:hover {
  background: rgba(99, 102, 241, 0.06);
}
.gcl-label--on {
  background: rgba(99, 102, 241, 0.12);
}
.gcl-check {
  appearance: none;
  -webkit-appearance: none;
  width: 22px;
  height: 22px;
  margin: 0;
  flex-shrink: 0;
  border-radius: 50%;
  border: 2px solid var(--accent, #6366f1);
  background: #fff;
  cursor: pointer;
  display: grid;
  place-content: center;
  transition: background 0.12s, box-shadow 0.12s;
}
.gcl-check:checked {
  background: var(--accent, #6366f1);
  box-shadow: inset 0 0 0 4px #fff;
}
.gcl-check:focus-visible {
  outline: 2px solid var(--accent, #6366f1);
  outline-offset: 2px;
}
.gcl-name {
  font-size: 0.95rem;
  font-weight: 500;
}
</style>
