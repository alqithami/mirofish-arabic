<template>
  <header class="app-header">
    <div class="header-left">
      <div class="brand" @click="router.push('/')">{{ t('common.appName') }}</div>
    </div>

    <div class="header-center">
      <div class="view-switcher">
        <button
          v-for="mode in viewModes"
          :key="mode"
          class="switch-btn"
          :class="{ active: viewMode === mode }"
          type="button"
          @click="$emit('update:viewMode', mode)"
        >
          {{ t(`common.viewModes.${mode}`) }}
        </button>
      </div>
    </div>

    <div class="header-right">
      <LanguageSwitcher />
      <div class="workflow-step">
        <span class="step-num">{{ t('common.stepIndicator', { current: stepNumber, total: totalSteps }) }}</span>
        <span class="step-name">{{ stepLabel }}</span>
      </div>
      <div class="step-divider"></div>
      <span class="status-indicator" :class="statusClass">
        <span class="dot"></span>
        {{ statusText }}
      </span>
    </div>
  </header>
</template>

<script setup>
import { useRouter } from 'vue-router'
import LanguageSwitcher from './LanguageSwitcher.vue'
import { useI18n } from '../i18n'

defineProps({
  viewMode: { type: String, required: true },
  stepNumber: { type: Number, required: true },
  totalSteps: { type: Number, default: 5 },
  stepLabel: { type: String, required: true },
  statusClass: { type: String, default: 'processing' },
  statusText: { type: String, required: true }
})

defineEmits(['update:viewMode'])

const router = useRouter()
const { t } = useI18n()
const viewModes = ['graph', 'split', 'workbench']
</script>

<style scoped>
.app-header {
  height: 60px;
  border-bottom: 1px solid #EAEAEA;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #FFF;
  z-index: 100;
  position: relative;
}

.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 18px;
  letter-spacing: 1px;
  cursor: pointer;
}

.view-switcher {
  display: flex;
  background: #F5F5F5;
  padding: 4px;
  border-radius: 6px;
  gap: 4px;
}

.switch-btn {
  border: none;
  background: transparent;
  padding: 6px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #666;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.switch-btn.active {
  background: #FFF;
  color: #000;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
  font-weight: 500;
  white-space: nowrap;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.workflow-step {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  white-space: nowrap;
}

.step-num {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: #999;
}

.step-name {
  font-weight: 700;
  color: #000;
}

.step-divider {
  width: 1px;
  height: 14px;
  background-color: #E0E0E0;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #CCC;
}

.status-indicator.processing .dot { background: #FF5722; animation: pulse 1s infinite; }
.status-indicator.completed .dot { background: #4CAF50; }
.status-indicator.error .dot { background: #F44336; }
.status-indicator.ready .dot { background: #4CAF50; }

@keyframes pulse { 50% { opacity: 0.5; } }

@media (max-width: 1200px) {
  .header-center {
    position: static;
    transform: none;
  }

  .app-header {
    flex-wrap: wrap;
    gap: 12px;
    height: auto;
    min-height: 60px;
    padding-block: 10px;
  }

  .header-right {
    width: 100%;
    justify-content: flex-end;
    flex-wrap: wrap;
  }
}
</style>
