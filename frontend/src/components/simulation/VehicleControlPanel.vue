<template>
  <v-card class="speed-panel pa-6 position-relative">
    <v-btn
      icon="mdi-close"
      variant="text"
      density="comfortable"
      class="close-button"
      @click="$emit('close')"
    />

    <div class="panel-title mb-5">Panel de control de velocidad</div>

    <section class="speed-section mb-4">
      <div class="section-label">Global velocidad</div>
      <div class="current-speed">Actual: {{ localConfig.velocidad_global }} Km/h</div>

      <v-slider
        v-model="localConfig.velocidad_global"
        color="#12c8ff"
        track-color="rgba(255,255,255,0.32)"
        :min="20"
        :max="120"
        :step="5"
        hide-details
        class="speed-slider"
        @update:model-value="setGlobalSpeed"
      />

      <div class="speed-range">
        <span>20 km/h</span>
        <span>120 km/h</span>
      </div>

      <div class="preset-grid mt-4">
        <button
          v-for="preset in speedPresets"
          :key="preset.label"
          class="preset-button"
          type="button"
          @click="setGlobalSpeed(preset.value)"
        >
          <v-icon :icon="preset.icon" size="42" />
          <span>{{ preset.label }}</span>
        </button>
      </div>
    </section>

    <section class="speed-section mb-6">
      <div class="section-label mb-6">Velocidad maxima por tipo (opcional)</div>

      <div class="vehicle-speed-grid">
        <label
          v-for="field in vehicleSpeedFields"
          :key="field.key"
          class="vehicle-speed-field"
        >
          <span>{{ field.label }}:</span>
          <select v-model.number="localConfig[field.key]">
            <option
              v-for="option in speedOptions"
              :key="`${field.key}-${option}`"
              :value="option"
            >
              {{ option }} Km/h
            </option>
          </select>
        </label>
      </div>
    </section>

    <div class="panel-actions">
      <v-btn color="primary" variant="flat" class="action-button" @click="apply">
        Aplicar cambios
      </v-btn>
      <v-btn color="#6d47ff" variant="flat" class="action-button" @click="cancel">
        Cancelar
      </v-btn>
    </div>
  </v-card>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'

const props = defineProps({
  config: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['update-config', 'close'])

const speedPresets = [
  { label: 'Lento', value: 35, icon: 'mdi-car-brake-alert' },
  { label: 'Medio', value: 70, icon: 'mdi-car' },
  { label: 'Rapido', value: 110, icon: 'mdi-car-turbocharger' },
]

const vehicleSpeedFields = [
  { label: 'Coche', key: 'velocidad_maxima_coche' },
  { label: 'Camion', key: 'velocidad_maxima_camion' },
  { label: 'Autobus', key: 'velocidad_maxima_autobus' },
  { label: 'Moto', key: 'velocidad_maxima_moto' },
]

const speedOptions = [40, 60, 80, 90, 100, 120, 140, 160]
const localConfig = reactive(createVehicleSpeedConfig(props.config))
const isDirty = ref(false)

watch(
  () => props.config,
  (value) => {
    if (isDirty.value) return
    Object.assign(localConfig, createVehicleSpeedConfig(value))
  },
  { deep: true },
)

watch(
  localConfig,
  () => {
    isDirty.value = true
  },
  { deep: true },
)

function createVehicleSpeedConfig(config) {
  return {
    ...config,
    velocidad_global: config.velocidad_global ?? 70,
    velocidad_promedio: config.velocidad_global ?? config.velocidad_promedio ?? 70,
    cambio_velocidad_individual: config.velocidad_global ?? config.cambio_velocidad_individual ?? 70,
    velocidad_maxima_coche: config.velocidad_maxima_coche ?? 120,
    velocidad_maxima_camion: config.velocidad_maxima_camion ?? 90,
    velocidad_maxima_autobus: config.velocidad_maxima_autobus ?? 100,
    velocidad_maxima_moto: config.velocidad_maxima_moto ?? 120,
  }
}

function setGlobalSpeed(speed) {
  localConfig.velocidad_global = speed
  localConfig.velocidad_promedio = speed
  localConfig.cambio_velocidad_individual = speed
}

function apply() {
  const speed = Number(localConfig.velocidad_global) || 0
  isDirty.value = false
  emit('update-config', {
    ...props.config,
    ...localConfig,
    velocidad_global: speed,
    velocidad_promedio: speed,
    cambio_velocidad_individual: speed,
  })
}

function cancel() {
  isDirty.value = false
  Object.assign(localConfig, createVehicleSpeedConfig(props.config))
  emit('close')
}
</script>

<style scoped>
.speed-panel {
  border: 1px solid rgba(173, 165, 255, 0.38) !important;
  background: #0d0828 !important;
  border-radius: 8px !important;
  box-shadow: 0 20px 60px rgba(2, 6, 23, 0.45) !important;
}

.close-button {
  position: absolute;
  top: 10px;
  right: 10px;
  color: #ffffff;
}

.panel-title {
  padding-right: 44px;
  color: #ffffff;
  font-size: 16px;
  font-weight: 650;
  text-transform: uppercase;
}

.speed-section {
  padding: 20px 26px;
  border: 1px solid #6947ff;
  border-radius: 8px;
  background: transparent;
  box-shadow: none;
}

.section-label {
  color: #ffffff;
  font-size: 13px;
  font-weight: 650;
  text-transform: uppercase;
}

.current-speed {
  margin-top: 4px;
  color: #ffffff;
  font-size: 16px;
  font-weight: 650;
  text-align: center;
}

.speed-slider {
  margin-top: 2px;
}

.speed-range {
  display: flex;
  justify-content: space-between;
  color: #ffffff;
  font-size: 10px;
  font-weight: 500;
}

.preset-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.preset-button {
  display: flex;
  min-height: 126px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid #6548f4;
  border-radius: 8px;
  background: transparent;
  color: #ffffff;
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  font-weight: 500;
  transition: border-color 0.18s ease, background 0.18s ease, transform 0.18s ease;
}

.preset-button:hover {
  border-color: #12c8ff;
  background: rgba(35, 21, 84, 0.56);
  transform: translateY(-1px);
}

.vehicle-speed-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 34px;
  row-gap: 22px;
}

.vehicle-speed-field {
  display: grid;
  grid-template-columns: 74px minmax(0, 1fr);
  align-items: center;
  gap: 8px;
  color: #ffffff;
  font-size: 13px;
  font-weight: 600;
}

.vehicle-speed-field select {
  width: 100%;
  min-height: 30px;
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 6px;
  background: #160f35;
  color: #ffffff;
  font: inherit;
  font-size: 12px;
  font-weight: 500;
  outline: none;
}

.panel-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 34px;
  padding: 0 14px;
}

.action-button {
  min-height: 36px;
  border-radius: 6px !important;
  font-size: 13px;
  font-weight: 650;
  text-transform: uppercase;
}

@media (max-width: 520px) {
  .speed-section {
    padding: 14px;
  }

  .preset-grid,
  .vehicle-speed-grid,
  .panel-actions {
    grid-template-columns: 1fr;
  }

  .vehicle-speed-field {
    grid-template-columns: 82px minmax(0, 1fr);
  }
}
</style>
