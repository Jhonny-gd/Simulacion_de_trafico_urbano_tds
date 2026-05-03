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
          background: '#150d3a',
          surface: '#25165c',
          primary: '#6f50ff',
          secondary: '#12c8ff',
          accent: '#7657ff',
          error: '#ff244f',
          success: '#18ff58',
          warning: '#ffe928',
        },
      },
    },
  },
})

createApp(App)
  .use(vuetify)
  .mount('#app')
