<template>
  <v-card class="panel-card pa-5">
    <div class="d-flex align-center justify-space-between mb-4">
      <div>
        <div class="text-subtitle-1 font-weight-bold">Control de vehiculos</div>
        <div class="text-caption muted-text">Ajustes operativos de flujo</div>
      </div>
      <v-icon color="primary" icon="mdi-car-cog" />
    </div>

    <v-slider
      v-model="localConfig.densidad_trafico"
      label="Densidad"
      color="primary"
      :min="0"
      :max="1"
      :step="0.01"
      thumb-label
      hide-details
      class="mb-5"
    />

    <v-slider
      v-model="localConfig.velocidad_promedio"
      label="Velocidad"
      color="secondary"
      :min="0"
      :max="35"
      :step="0.5"
      thumb-label
      hide-details
      class="mb-5"
    />

    <v-select
      v-model="localConfig.tipo_vehiculo"
      :items="vehicleTypes"
      label="Tipo de vehiculo"
      variant="outlined"
      density="compact"
      hide-details
      class="mb-4"
    />

    <v-btn block color="primary" prepend-icon="mdi-content-save-outline" @click="apply">
      Aplicar cambios
    </v-btn>
  </v-card>
</template>

<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  config: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['update-config'])

const vehicleTypes = ['car', 'bus', 'truck', 'motorcycle', 'emergency']
const localConfig = reactive({ ...props.config })

watch(
  () => props.config,
  (value) => Object.assign(localConfig, value),
  { deep: true },
)

function apply() {
  emit('update-config', { ...props.config, ...localConfig })
}
</script>
