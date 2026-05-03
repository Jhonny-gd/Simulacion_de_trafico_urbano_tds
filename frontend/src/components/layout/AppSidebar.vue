<template>
  <v-navigation-drawer
    :model-value="true"
    color="#0d0828"
    width="260"
    class="border-e-sm border-opacity-25"
    permanent
  >
    <div class="pa-5">
      <div class="d-flex align-center ga-3">
        <v-avatar color="primary" rounded="lg">
          <v-icon icon="mdi-road-variant" />
        </v-avatar>
        <div>
          <div class="font-weight-bold">Traffic SaaS</div>
          <div class="text-caption muted-text">Webots Control</div>
        </div>
      </div>
    </div>

    <v-list nav density="comfortable" class="px-3">
      <v-list-item
        v-for="item in items"
        :key="item.value"
        :active="activeSection === item.value"
        :prepend-icon="item.icon"
        :title="item.title"
        color="primary"
        rounded="lg"
        @click="$emit('select-section', item.value)"
      />
    </v-list>
  </v-navigation-drawer>
</template>

<script setup>
defineProps({
  activeSection: {
    type: String,
    required: true,
  },
})

defineEmits(['select-section'])

const items = [
  { title: 'Dashboard', value: 'dashboard', icon: 'mdi-view-dashboard-outline' },
  { title: 'Control', value: 'control', icon: 'mdi-tune-variant' },
  { title: 'Vehiculos', value: 'vehicles', icon: 'mdi-car-multiple' },
  { title: 'Semaforos', value: 'trafficLights', icon: 'mdi-traffic-light' },
  { title: 'Monitoreo', value: 'monitoring', icon: 'mdi-chart-line' },
]
</script>
