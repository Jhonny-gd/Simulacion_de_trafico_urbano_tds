<template>
  <v-card class="panel-card pa-5">
    <div class="d-flex align-center justify-space-between mb-4">
      <div>
        <div class="text-subtitle-1 font-weight-bold">Control de semaforos</div>
        <div class="text-caption muted-text">Ciclo automatico o manual</div>
      </div>
      <v-icon color="accent" icon="mdi-traffic-light" />
    </div>

    <v-switch
      v-model="localConfig.modo_automatico_semaforo"
      color="success"
      label="Modo automatico"
      hide-details
      class="mb-2"
    />

    <v-slider
      v-model="localConfig.tiempo_luz_verde"
      label="Luz verde"
      color="success"
      :min="1"
      :max="120"
      :step="1"
      thumb-label
      hide-details
      class="mb-5"
    />

    <v-slider
      v-model="localConfig.tiempo_luz_roja"
      label="Luz roja"
      color="error"
      :min="1"
      :max="120"
      :step="1"
      thumb-label
      hide-details
      class="mb-5"
    />

    <div class="d-flex ga-2 mb-4">
      <v-btn color="success" variant="flat" class="flex-1-1" @click="setLight('green')">
        Verde
      </v-btn>
      <v-btn color="error" variant="flat" class="flex-1-1" @click="setLight('red')">
        Rojo
      </v-btn>
    </div>

    <v-btn block color="accent" prepend-icon="mdi-content-save-outline" @click="apply">
      Guardar semaforo
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
const localConfig = reactive({ ...props.config })

watch(
  () => props.config,
  (value) => Object.assign(localConfig, value),
  { deep: true },
)

function setLight(state) {
  localConfig.modo_automatico_semaforo = false
  localConfig.estado_semaforo = state
  apply()
}

function apply() {
  emit('update-config', { ...props.config, ...localConfig })
}
</script>
