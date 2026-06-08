import 'element-plus/dist/index.css'
import './styles/main.css'

import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'

document.documentElement.dataset.theme = localStorage.getItem('theme') || 'light'

createApp(App).use(createPinia()).use(router).mount('#app')
