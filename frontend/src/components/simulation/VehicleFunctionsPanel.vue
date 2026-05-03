<template>
  <v-card class="vehicle-panel pa-5 position-relative">
    <v-btn
      icon="mdi-close"
      variant="text"
      density="comfortable"
      class="close-button"
      @click="$emit('close')"
    />

    <div class="vehicle-title">Funciones de vehiculo</div>

    <section class="vehicle-form mt-4">
      <div class="form-row">
        <div class="row-icon">
          <v-icon icon="mdi-car" size="26" />
        </div>
        <div class="row-copy">
          <div class="row-title">Tipo de vehiculo</div>
          <div class="row-help">Seleccionar tipo</div>
        </div>
        <v-select
          v-model="localConfig.tipo_vehiculo"
          :items="vehicleTypes"
          item-title="label"
          item-value="value"
          variant="outlined"
          density="compact"
          hide-details
          class="row-control"
        />
      </div>

      <div class="form-row">
        <div class="row-icon">
          <v-icon icon="mdi-swap-vertical" size="26" />
        </div>
        <div class="row-copy">
          <div class="row-title">Direccion del vehiculo</div>
          <div class="row-help">Ruta de movimiento</div>
        </div>
        <div class="direction-group row-control">
          <button
            v-for="direction in directions"
            :key="direction.value"
            :class="['mini-action', { active: localConfig.direccion_vehiculo === direction.value }]"
            type="button"
            @click="localConfig.direccion_vehiculo = direction.value"
          >
            <v-icon :icon="direction.icon" size="18" />
            <span>{{ direction.label }}</span>
          </button>
        </div>
      </div>

      <div class="form-row">
        <div class="row-icon">
          <v-icon icon="mdi-speedometer" size="26" />
        </div>
        <div class="row-copy">
          <div class="row-title">Cambio de velocidad</div>
          <div class="row-help">Ajustar velocidad del vehiculo</div>
        </div>
        <div class="speed-control row-control">
          <v-btn icon="mdi-minus" size="x-small" color="primary" @click="adjustSpeed(-5)" />
          <v-slider
            v-model="localConfig.cambio_velocidad_individual"
            color="#12c8ff"
            track-color="rgba(255,255,255,0.28)"
            :min="0"
            :max="120"
            :step="5"
            hide-details
          />
          <span class="speed-value">{{ localConfig.cambio_velocidad_individual }} km/h</span>
          <v-btn icon="mdi-plus" size="x-small" color="primary" @click="adjustSpeed(5)" />
        </div>
      </div>

      <div class="form-row">
        <div class="row-icon">
          <v-icon icon="mdi-lightbulb-outline" size="26" />
        </div>
        <div class="row-copy">
          <div class="row-title">Senales del vehiculo</div>
          <div class="row-help">Luces e indicadores</div>
        </div>
        <div class="signal-group row-control">
          <button
            v-for="signal in signals"
            :key="signal.value"
            :class="['signal-action', signal.color, { active: localConfig.senales_vehiculo[signal.value] }]"
            type="button"
            @click="toggleSignal(signal.value)"
          >
            <v-icon :icon="signal.icon" size="20" />
            <span>{{ signal.label }}</span>
          </button>
        </div>
      </div>

      <div class="form-row">
        <div class="row-icon">
          <v-icon icon="mdi-pulse" size="26" />
        </div>
        <div class="row-copy">
          <div class="row-title">Estado del vehiculo</div>
          <div class="row-help">Informacion actual</div>
        </div>
        <div class="status-group row-control">
          <span class="status-pill active-state"><span />Activo</span>
          <span class="status-pill"><v-icon icon="mdi-speedometer" size="18" />{{ localConfig.cambio_velocidad_individual }}km/h</span>
          <span class="status-pill"><v-icon icon="mdi-gas-station" size="18" />78%</span>
        </div>
      </div>

      <div class="form-row">
        <div class="row-icon">
          <v-icon icon="mdi-monitor-screenshot" size="26" />
        </div>
        <div class="row-copy">
          <div class="row-title">Control individual</div>
          <div class="row-help">Seleccionar vehiculo</div>
        </div>
        <div class="individual-control row-control">
          <v-select
            v-model="localConfig.vehiculo_seleccionado"
            :items="vehicleOptions"
            item-title="label"
            item-value="value"
            variant="outlined"
            density="compact"
            hide-details
          />
          <v-btn color="#7657ff" variant="flat" prepend-icon="mdi-crosshairs-gps">
            Ver en mapa
          </v-btn>
        </div>
      </div>
    </section>

    <div class="vehicle-actions mt-5">
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
import { computed, reactive, watch } from 'vue'

const props = defineProps({
  config: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['update-config', 'close'])

const vehicleTypes = [
  { label: 'Sedan', value: 'sedan' },
  { label: 'Camion', value: 'camion' },
  { label: 'Autobus', value: 'autobus' },
  { label: 'Motocicleta', value: 'motocicleta' },
]

const directions = [
  { label: 'Izquierda', value: 'left', icon: 'mdi-arrow-left' },
  { label: 'Recto', value: 'straight', icon: 'mdi-arrow-up' },
  { label: 'Derecha', value: 'right', icon: 'mdi-arrow-right' },
]

const signals = [
  { label: 'Luces', value: 'luces', icon: 'mdi-car-light-high', color: 'yellow' },
  { label: 'Direccional', value: 'direccional', icon: 'mdi-arrow-left-right', color: 'green' },
  { label: 'Bocina', value: 'bocina', icon: 'mdi-bullhorn-outline', color: 'blue' },
  { label: 'Emergencia', value: 'emergencia', icon: 'mdi-alert-octagon-outline', color: 'red' },
]

const localConfig = reactive(createVehicleConfig(props.config))

const vehicleOptions = computed(() => {
  const vehicleCount = Math.max(Number(props.config.conteo_vehiculos) || 0, 1)

  return Array.from({ length: vehicleCount }, (_, index) => {
    const number = String(index + 1).padStart(2, '0')
    return {
      label: `Veh ${number}`,
      value: `veh_${number}`,
    }
  })
})

watch(
  () => props.config,
  (value) => Object.assign(localConfig, createVehicleConfig(value)),
  { deep: true },
)

function createVehicleConfig(config) {
  return {
    ...config,
    tipo_vehiculo: normalizeVehicleType(config.tipo_vehiculo),
    direccion_vehiculo: config.direccion_vehiculo ?? 'straight',
    cambio_velocidad_individual: config.cambio_velocidad_individual ?? 45,
    senales_vehiculo: normalizeVehicleSignals(config.senales_vehiculo),
    vehiculo_seleccionado: config.vehiculo_seleccionado ?? 'veh_01',
  }
}

function normalizeVehicleSignals(signalsValue) {
  const defaults = {
    luces: false,
    direccional: false,
    bocina: false,
    emergencia: false,
  }

  if (typeof signalsValue === 'string') {
    if (!Object.prototype.hasOwnProperty.call(defaults, signalsValue)) {
      return defaults
    }

    return {
      ...defaults,
      [signalsValue]: true,
    }
  }

  return {
    ...defaults,
    ...(signalsValue ?? {}),
  }
}

function normalizeVehicleType(type) {
  const legacyMap = {
    car: 'sedan',
    truck: 'camion',
    bus: 'autobus',
    motorcycle: 'motocicleta',
  }

  return legacyMap[type] ?? type ?? 'sedan'
}

function adjustSpeed(delta) {
  const nextSpeed = Number(localConfig.cambio_velocidad_individual) + delta
  localConfig.cambio_velocidad_individual = Math.min(Math.max(nextSpeed, 0), 120)
}

function toggleSignal(signal) {
  localConfig.senales_vehiculo[signal] = !localConfig.senales_vehiculo[signal]
}

function apply() {
  emit('update-config', { ...props.config, ...localConfig })
}

function cancel() {
  Object.assign(localConfig, createVehicleConfig(props.config))
}
</script>

<style scoped>
.vehicle-panel {
  border: 1px solid rgba(173, 165, 255, 0.38) !important;
  background: #0d0828 !important;
  border-radius: 8px !important;
  box-shadow: 0 20px 60px rgba(2, 6, 23, 0.45) !important;
  overflow: hidden;
}

.close-button {
  position: absolute;
  top: 10px;
  right: 10px;
  color: #ffffff;
}

.vehicle-title {
  padding-right: 44px;
  color: #ffffff;
  font-size: 17px;
  font-weight: 650;
  text-transform: uppercase;
}

.vehicle-form {
  display: grid;
  gap: 22px;
  padding: 24px 24px;
  border: 1px solid #6947ff;
  border-radius: 8px;
  background: rgba(26, 16, 65, 0.92);
}

.form-row {
  display: grid;
  grid-template-columns: 42px minmax(160px, 0.72fr) minmax(320px, 1.45fr);
  align-items: center;
  gap: 14px;
  min-height: 54px;
  min-width: 0;
}

.row-icon {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  border-radius: 8px;
  background: #6f50ff;
  color: #ffffff;
}

.row-copy {
  min-width: 0;
}

.row-title {
  color: #ffffff;
  font-size: 14px;
  font-weight: 650;
  line-height: 1.1;
  text-transform: uppercase;
}

.row-help {
  margin-top: 2px;
  color: rgba(255, 255, 255, 0.82);
  font-size: 11px;
}

.row-control {
  min-width: 0;
}

.direction-group,
.signal-group,
.status-group,
.individual-control,
.speed-control {
  display: flex;
  align-items: center;
  gap: 10px;
}

.direction-group {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.mini-action,
.signal-action {
  border: 1px solid #6548f4;
  border-radius: 5px;
  background: rgba(35, 21, 84, 0.9);
  color: #ffffff;
  cursor: pointer;
  font: inherit;
}

.mini-action {
  display: flex;
  min-width: 0;
  min-height: 34px;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 2px 6px;
  font-size: 9px;
}

.mini-action.active,
.signal-action.active {
  border-color: #12c8ff;
  box-shadow: 0 0 0 1px rgba(18, 200, 255, 0.22);
}

.speed-control {
  display: grid;
  grid-template-columns: 28px minmax(120px, 1fr) 64px 28px;
  min-width: 0;
}

.speed-value {
  color: #ffffff;
  font-size: 11px;
  font-weight: 650;
  white-space: nowrap;
}

.signal-group {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.signal-action {
  display: flex;
  min-width: 0;
  min-height: 38px;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 4px 6px;
  font-size: 10px;
}

.signal-action.yellow {
  color: #ffd800;
}

.signal-action.green {
  color: #22ff5d;
}

.signal-action.blue {
  color: #16baff;
}

.signal-action.red {
  color: #ff244f;
}

.status-pill {
  display: inline-flex;
  min-height: 28px;
  align-items: center;
  gap: 6px;
  padding: 0 10px;
  border: 1px solid #6548f4;
  border-radius: 5px;
  color: #ffffff;
  font-size: 11px;
  white-space: nowrap;
}

.active-state span {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #18ff58;
}

.individual-control {
  display: grid;
  grid-template-columns: minmax(150px, 1fr) minmax(120px, auto);
  min-width: 0;
}

.vehicle-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 60px;
  padding: 8px 12px 4px;
}

.action-button {
  min-height: 36px;
  border-radius: 6px !important;
  font-size: 13px;
  font-weight: 650;
  text-transform: uppercase;
}

@media (max-width: 720px) {
  .form-row {
    grid-template-columns: 42px minmax(0, 1fr);
  }

  .row-control {
    grid-column: 1 / -1;
  }

  .vehicle-actions {
    gap: 18px;
  }
}

@media (max-width: 520px) {
  .vehicle-title {
    font-size: 15px;
  }

  .vehicle-form {
    padding: 14px;
  }

  .direction-group {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .signal-group,
  .status-group {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .individual-control,
  .vehicle-actions {
    grid-template-columns: 1fr;
  }

  .speed-control {
    grid-template-columns: 28px minmax(0, 1fr) 52px 28px;
  }

  .mini-action span,
  .signal-action span {
    font-size: 8px;
  }
}
</style>
