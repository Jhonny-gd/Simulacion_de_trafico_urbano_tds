<template>
  <v-app-bar color="#0d0828" flat height="72" class="border-b-sm border-opacity-25 px-4">
    <div>
      <div class="text-h6 font-weight-bold">Simulacion de trafico urbano</div>
      <div class="text-caption muted-text">Backend: {{ apiState }}</div>
    </div>

    <v-spacer />

    <div class="d-flex align-center ga-2">
      <v-chip :color="stateColor" variant="flat" size="small">
        {{ simulationState }}
      </v-chip>
      <v-btn class="control-button" color="success" prepend-icon="mdi-play" @click="$emit('start')">
        Iniciar
      </v-btn>
      <v-btn class="control-button" color="secondary" prepend-icon="mdi-pause" @click="$emit('pause')">
        Pausar
      </v-btn>
      <v-btn class="control-button" color="error" prepend-icon="mdi-restart" @click="$emit('reset')">
        Reset
      </v-btn>
      <v-btn icon="mdi-logout" variant="text" @click="$emit('logout')" />
    </div>
  </v-app-bar>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  simulationState: {
    type: String,
    default: 'stopped',
  },
  apiOnline: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['start', 'pause', 'reset', 'logout'])

const apiState = computed(() => (props.apiOnline ? 'conectado' : 'sin conexion'))
const stateColor = computed(() => {
  if (props.simulationState === 'running') return 'success'
  if (props.simulationState === 'paused') return 'secondary'
  return 'error'
})
</script>
