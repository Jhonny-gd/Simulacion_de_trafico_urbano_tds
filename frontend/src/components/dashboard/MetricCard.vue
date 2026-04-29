<template>
  <v-card class="surface-card pa-5 h-100">
    <div class="d-flex align-start justify-space-between">
      <div>
        <div class="text-body-2 muted-text mb-2">{{ label }}</div>
        <div class="text-h4 font-weight-bold">{{ value }}</div>
      </div>
      <v-avatar :color="color" rounded="lg" size="42">
        <v-icon :icon="icon" />
      </v-avatar>
    </div>
    <div class="text-caption muted-text mt-4">{{ detail }}</div>
  </v-card>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  detail: { type: String, default: '' },
  icon: { type: String, required: true },
  color: { type: String, default: 'primary' },
})
</script>
