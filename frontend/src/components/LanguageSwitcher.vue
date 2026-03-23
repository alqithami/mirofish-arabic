<template>
  <div class="language-switcher" role="group" :aria-label="t('common.appName') + ' language switcher'">
    <button
      v-for="item in availableLocales"
      :key="item.code"
      class="lang-btn"
      :class="{ active: locale === item.code }"
      type="button"
      @click="setLocale(item.code)"
    >
      {{ item.label }}
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from '../i18n'

const { locale: currentLocale, setLocale, t, availableLocales } = useI18n()
const locale = computed(() => currentLocale.value)
</script>

<style scoped>
.language-switcher {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  margin-inline-start: 12px;
}

.lang-btn {
  border: none;
  background: transparent;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  color: #444;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.lang-btn:hover {
  background: rgba(0, 0, 0, 0.05);
}

.lang-btn.active {
  background: #000;
  color: #fff;
}
</style>
