import { createApp } from 'vue'
import App from './App.vue'
import './style.css'

import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'trafficDark',
    themes: {
      trafficDark: {
        dark: true,
        colors: {
          background: '#0f172a',
          surface: '#1e293b',
          primary: '#3b82f6',
          secondary: '#06b6d4',
          accent: '#8b5cf6',
          error: '#ef4444',
          success: '#22c55e',
        },
      },
    },
  },
})

createApp(App)
  .use(vuetify)
  .mount('#app')
