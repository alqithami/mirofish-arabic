import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createMiroI18n } from './i18n'

const app = createApp(App)

app.use(createMiroI18n())
app.use(router)

app.mount('#app')
