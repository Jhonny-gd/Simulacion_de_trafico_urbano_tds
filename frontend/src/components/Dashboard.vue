<template>
  <v-container fluid class="pa-6" style="background:#0f172a; min-height:100vh;">
    
    <h1 class="text-white mb-6">Simulación de Tráfico Urbano</h1>

    <v-row>
      <v-col cols="4">
        <v-card class="pa-4" color="#1e293b">
          <h3 class="text-white">Vehículos</h3>
          <h1 class="text-white">{{ data.vehiculos }}</h1>
        </v-card>
      </v-col>

      <v-col cols="4">
        <v-card class="pa-4" color="#1e293b">
          <h3 class="text-white">Semáforo</h3>
          <h1 :class="data.semaforo === 'RED' ? 'text-red' : 'text-green'">
            {{ data.semaforo }}
          </h1>
        </v-card>
      </v-col>

      <v-col cols="4">
        <v-card class="pa-4" color="#1e293b">
          <h3 class="text-white">Congestión</h3>
          <h1 class="text-white">{{ data.congestion }}</h1>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-6">
      <v-col cols="12">
        <v-card height="300" color="#1e293b" class="d-flex align-center justify-center">
          <span class="text-white">Vista de simulación (Webots)</span>
        </v-card>
      </v-col>
    </v-row>

  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const data = ref({
  vehiculos: 0,
  congestion: 0,
  semaforo: ''
})

const loadData = async () => {
  const res = await axios.get('http://127.0.0.1:8000/simulation')
  data.value = res.data
}

onMounted(() => {
  loadData()

  // actualizar cada 2 segundos
  setInterval(loadData, 2000)
})
</script>