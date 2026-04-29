<template>
  <v-card class="panel-card pa-5">
    <div class="d-flex align-center justify-space-between mb-5">
      <div>
        <div class="text-subtitle-1 font-weight-bold">Monitoreo</div>
        <div class="text-caption muted-text">Metricas en tiempo real</div>
      </div>
      <v-icon color="secondary" icon="mdi-chart-timeline-variant" />
    </div>

    <v-list bg-color="transparent" density="compact">
      <v-list-item
        v-for="metric in metrics"
        :key="metric.label"
        class="px-0"
      >
        <template #prepend>
          <v-icon :color="metric.color" :icon="metric.icon" />
        </template>
        <v-list-item-title>{{ metric.label }}</v-list-item-title>
        <template #append>
          <span class="font-weight-bold">{{ metric.value }}</span>
        </template>
      </v-list-item>
    </v-list>
  </v-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  config: {
    type: Object,
    required: true,
  },
  simulationState: {
    type: String,
    default: 'stopped',
  },
})

const metrics = computed(() => [
  { label: 'Estado', value: props.simulationState, icon: 'mdi-pulse', color: 'primary' },
  { label: 'Vehiculos', value: props.config.conteo_vehiculos ?? 0, icon: 'mdi-car-multiple', color: 'primary' },
  { label: 'Densidad', value: props.config.densidad_trafico ?? 0, icon: 'mdi-map-marker-distance', color: 'secondary' },
  { label: 'Velocidad', value: `${props.config.velocidad_promedio ?? 0} m/s`, icon: 'mdi-speedometer', color: 'success' },
  { label: 'Flujo', value: props.config.flujo_vehicular ?? 0, icon: 'mdi-transit-connection', color: 'accent' },
  { label: 'Congestion', value: `${props.config.nivel_congestion ?? 0}%`, icon: 'mdi-alert-circle-outline', color: 'error' },
])
</script>
