<template>
  <router-view />
</template>

<script setup>
// Route shell only.
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body,
#app {
  min-height: 100%;
}

body {
  font-family: 'JetBrains Mono', 'Noto Sans Arabic', 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #000000;
  background-color: #ffffff;
}

#app {
  color: #000000;
  background-color: #ffffff;
}

html[dir='rtl'] body,
html[dir='rtl'] #app {
  direction: rtl;
  text-align: right;
}

html[dir='rtl'] input,
html[dir='rtl'] textarea,
html[dir='rtl'] .code-input,
html[dir='rtl'] .modal-requirement,
html[dir='rtl'] .modal-file-name,
html[dir='rtl'] .card-title,
html[dir='rtl'] .card-desc,
html[dir='rtl'] .detail-content,
html[dir='rtl'] .description,
html[dir='rtl'] .section-desc,
html[dir='rtl'] .hero-desc,
html[dir='rtl'] .step-desc,
html[dir='rtl'] .workflow-item,
html[dir='rtl'] .console-header,
html[dir='rtl'] .panel-header,
html[dir='rtl'] .modal-section {
  text-align: right;
}

html[dir='rtl'] .github-link,
html[dir='rtl'] .workflow-step,
html[dir='rtl'] .step-info,
html[dir='rtl'] .console-header,
html[dir='rtl'] .header-tools,
html[dir='rtl'] .header-right,
html[dir='rtl'] .nav-links,
html[dir='rtl'] .metric-card,
html[dir='rtl'] .card-header,
html[dir='rtl'] .card-footer,
html[dir='rtl'] .modal-header,
html[dir='rtl'] .modal-actions,
html[dir='rtl'] .detail-row {
  flex-direction: row-reverse;
}

html[dir='rtl'] .btn-arrow,
html[dir='rtl'] .conn-arrow,
html[dir='rtl'] .arrow {
  transform: scaleX(-1);
  display: inline-block;
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #000000;
}

::-webkit-scrollbar-thumb:hover {
  background: #333333;
}

button {
  font-family: inherit;
}
</style>
