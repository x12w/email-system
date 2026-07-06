import 'element-plus/dist/index.css'
import './styles/main.css'

import ElementPlus from 'element-plus'
import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'

document.documentElement.dataset.theme = localStorage.getItem('theme') || 'light'

createApp(App).use(createPinia()).use(ElementPlus).use(router).mount('#app')
