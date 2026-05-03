<template>
  <v-card class="traffic-panel pa-5 position-relative">
    <v-btn
      icon="mdi-close"
      variant="text"
      density="comfortable"
      class="close-button"
      @click="$emit('close')"
    />

    <header class="traffic-header">
      <div class="traffic-title">Control de semaforos</div>
      <div class="traffic-dots" aria-hidden="true">
        <span class="green" />
        <span class="yellow" />
        <span class="red" />
      </div>
    </header>

    <section class="traffic-content">
      <h2>Panel de semaforos</h2>

      <div class="traffic-grid">
        <article class="traffic-card current-card">
          <div class="section-label">Estado actual</div>
          <div class="current-state-row">
            <div>
              <div :class="['current-state', localConfig.estado_semaforo]">
                {{ currentStateLabel }}
              </div>
              <div class="small-help">{{ currentStateHelp }}</div>
              <div class="phase-help">Fase {{ currentPhaseLabel }}</div>
            </div>
          </div>

          <div class="remaining-label">
            Tiempo restante
            <v-icon icon="mdi-timer-sand" size="15" />
          </div>
          <div :class="['remaining-time', localConfig.estado_semaforo]">
            {{ remainingTime }}
          </div>
          <div class="small-help">Segundos</div>
        </article>

        <article class="traffic-card timing-card">
          <div class="section-label">Tiempos del semaforo</div>

          <div class="time-row">
            <span class="state-dot red" />
            <div class="time-copy">
              <div class="time-title">Tiempo de luz roja</div>
              <div class="small-help">Duracion en segundos</div>
            </div>
          </div>
          <div class="slider-row">
            <span>5</span>
            <v-slider
              v-model="localConfig.tiempo_luz_roja"
              color="#ff202b"
              track-color="rgba(255,255,255,0.34)"
              :min="5"
              :max="120"
              :step="5"
              hide-details
            />
            <span>120</span>
            <span class="value-box">{{ localConfig.tiempo_luz_roja }} seg</span>
          </div>

          <div class="time-row mt-3">
            <span class="state-dot green" />
            <div class="time-copy">
              <div class="time-title">Tiempo de luz verde</div>
              <div class="small-help">Duracion en segundos</div>
            </div>
          </div>
          <div class="slider-row">
            <span>5</span>
            <v-slider
              v-model="localConfig.tiempo_luz_verde"
              color="#18ff58"
              track-color="rgba(255,255,255,0.34)"
              :min="5"
              :max="120"
              :step="5"
              hide-details
            />
            <span>120</span>
            <span class="value-box">{{ localConfig.tiempo_luz_verde }} seg</span>
          </div>
        </article>
      </div>

      <article class="traffic-card mode-card">
        <div class="section-label">Modo de control</div>
        <div class="mode-grid">
          <button
            :class="['mode-option', { active: localConfig.modo_automatico_semaforo }]"
            type="button"
            @click="setMode(true)"
          >
            <v-icon icon="mdi-clock-time-three-outline" size="34" />
            <span>
              <strong>Automatico</strong>
              <small>El sistema ajusta los tiempos segun flujo vehicular</small>
            </span>
            <v-switch
              :model-value="localConfig.modo_automatico_semaforo"
              color="primary"
              hide-details
              inset
              readonly
            />
          </button>

          <button
            :class="['mode-option', { active: !localConfig.modo_automatico_semaforo }]"
            type="button"
            @click="setMode(false)"
          >
            <v-icon icon="mdi-hand-back-right-outline" size="34" />
            <span>
              <strong>Manual</strong>
              <small>Controla los tiempos de forma manual</small>
            </span>
            <v-switch
              :model-value="!localConfig.modo_automatico_semaforo"
              color="primary"
              hide-details
              inset
              readonly
            />
          </button>
        </div>
      </article>

      <article class="traffic-card quick-card">
        <div class="section-label">Acciones rapidas</div>
        <div class="quick-grid">
          <button class="quick-action green-action" type="button" @click="setLight('green')">
            <span>
              <strong>Poner en verde</strong>
              <small>Activar luz verde</small>
            </span>
            <span class="state-dot green" />
          </button>
          <button class="quick-action red-action" type="button" @click="setLight('red')">
            <span>
              <strong>Poner en rojo</strong>
              <small>Activar luz roja</small>
            </span>
            <span class="state-dot red" />
          </button>
          <button class="quick-action yellow-action" type="button" @click="toggleLight">
            <span>
              <strong>Cambiar ahora</strong>
              <small>Alternar estado</small>
            </span>
            <v-icon icon="mdi-sync" size="26" />
          </button>
          <button class="quick-action reset-action" type="button" @click="resetCycle">
            <span>
              <strong>Reiniciar ciclo</strong>
              <small>Restablecer tiempos</small>
            </span>
            <v-icon icon="mdi-reload" size="25" />
          </button>
        </div>
      </article>

      <div class="traffic-actions">
        <v-btn color="primary" variant="flat" class="action-button" @click="apply">
          Aplicar cambios
        </v-btn>
        <v-btn color="#6d47ff" variant="flat" class="action-button" @click="$emit('close')">
          Cerrar
        </v-btn>
      </div>
    </section>
  </v-card>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  config: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['update-config', 'close'])
const localConfig = reactive(createTrafficConfig(props.config))
const isDirty = ref(false)
const isSyncing = ref(false)

const stateLabels = {
  red: 'Rojo',
  yellow: 'Amarillo',
  green: 'Verde',
}

const stateHelp = {
  red: 'Detener transito',
  yellow: 'Precaucion',
  green: 'Avanzar transito',
}

const currentStateLabel = computed(() => stateLabels[localConfig.estado_semaforo] ?? 'Rojo')
const currentStateHelp = computed(() => stateHelp[localConfig.estado_semaforo] ?? 'Detener transito')
const currentPhaseLabel = computed(() => {
  const labels = {
    north_south: 'Norte-Sur',
    east_west: 'Este-Oeste',
  }

  return labels[localConfig.fase_semaforo] ?? 'Norte-Sur'
})
const remainingTime = computed(() => {
  if (localConfig.tiempo_restante_semaforo !== undefined) {
    return formatTime(localConfig.tiempo_restante_semaforo)
  }
  if (localConfig.estado_semaforo === 'green') return formatTime(localConfig.tiempo_luz_verde)
  if (localConfig.estado_semaforo === 'yellow') return '00:05'
  return formatTime(localConfig.tiempo_luz_roja)
})

watch(
  () => props.config,
  (value) => {
    if (isDirty.value) return

    isSyncing.value = true
    Object.assign(localConfig, createTrafficConfig(value))
    isSyncing.value = false
  },
  { deep: true },
)

watch(
  localConfig,
  () => {
    if (isSyncing.value) return
    isDirty.value = true
  },
  { deep: true },
)

function createTrafficConfig(config) {
  return {
    ...config,
    estado_semaforo: config.estado_semaforo ?? 'red',
    fase_semaforo: config.fase_semaforo ?? 'north_south',
    tiempo_luz_verde: config.tiempo_luz_verde ?? 60,
    tiempo_luz_roja: config.tiempo_luz_roja ?? 45,
    tiempo_restante_semaforo: config.tiempo_restante_semaforo,
    modo_automatico_semaforo: config.modo_automatico_semaforo ?? true,
  }
}

function formatTime(seconds) {
  const value = Math.max(Math.floor(Number(seconds) || 0), 0)
  const minutes = Math.floor(value / 60)
  const rest = String(value % 60).padStart(2, '0')
  return `0${minutes}:${rest}`
}

function setMode(isAutomatic) {
  localConfig.modo_automatico_semaforo = isAutomatic

  if (isAutomatic) {
    localConfig.control_manual_semaforo = null
    localConfig.estado_semaforo = 'green'
    return
  }

  localConfig.control_manual_semaforo = localConfig.estado_semaforo ?? 'red'
}

function setLight(state) {
  localConfig.modo_automatico_semaforo = false
  localConfig.estado_semaforo = state
  localConfig.control_manual_semaforo = state
}

function toggleLight() {
  if (localConfig.modo_automatico_semaforo) {
    localConfig.fase_semaforo = localConfig.fase_semaforo === 'north_south' ? 'east_west' : 'north_south'
    return
  }

  setLight(localConfig.estado_semaforo === 'green' ? 'red' : 'green')
}

function resetCycle() {
  localConfig.tiempo_luz_roja = 45
  localConfig.tiempo_luz_verde = 60
  localConfig.estado_semaforo = 'red'
  localConfig.fase_semaforo = 'north_south'
  localConfig.control_manual_semaforo = localConfig.modo_automatico_semaforo ? null : 'red'
}

function apply() {
  const isAutomatic = Boolean(localConfig.modo_automatico_semaforo)
  isDirty.value = false
  emit('update-config', {
    ...props.config,
    ...localConfig,
    tiempo_luz_verde: Number(localConfig.tiempo_luz_verde) || 30,
    tiempo_luz_roja: Number(localConfig.tiempo_luz_roja) || 30,
    fase_semaforo: localConfig.fase_semaforo ?? 'north_south',
    estado_semaforo: localConfig.estado_semaforo ?? 'red',
    modo_automatico_semaforo: isAutomatic,
    control_manual_semaforo: isAutomatic ? null : localConfig.estado_semaforo ?? 'red',
  })
}
</script>

<style scoped>
.traffic-panel {
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
  z-index: 2;
}

.traffic-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin: -20px -20px 0;
  padding: 24px 66px 16px 36px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.64);
}

.traffic-title,
.traffic-content h2 {
  color: #ffffff;
  font-weight: 650;
  text-transform: uppercase;
}

.traffic-title {
  font-size: 17px;
}

.traffic-content {
  padding: 30px 10px 4px;
}

.traffic-content h2 {
  margin: 0 0 18px;
  font-size: 17px;
}

.traffic-dots {
  display: flex;
  gap: 16px;
}

.traffic-dots span,
.state-dot {
  display: inline-block;
  width: 17px;
  height: 17px;
  flex: 0 0 auto;
  border-radius: 999px;
}

.traffic-dots .green,
.state-dot.green {
  background: #18ff58;
}

.traffic-dots .yellow,
.state-dot.yellow {
  background: #ffe928;
}

.traffic-dots .red,
.state-dot.red {
  background: #ff202b;
}

.traffic-grid {
  display: grid;
  grid-template-columns: minmax(210px, 0.9fr) minmax(330px, 1.2fr);
  gap: 14px;
}

.traffic-card {
  border: 1px solid #6947ff;
  border-radius: 8px;
  background: rgba(26, 16, 65, 0.94);
}

.current-card,
.timing-card,
.mode-card,
.quick-card {
  padding: 20px 22px;
}

.section-label {
  color: #00a8ff;
  font-size: 14px;
  font-weight: 650;
  text-transform: uppercase;
}

.current-state-row {
  display: flex;
  align-items: center;
  margin-top: 12px;
}

.current-state {
  color: #ffffff;
  font-size: 20px;
  font-weight: 650;
  line-height: 1.1;
  text-transform: uppercase;
}

.current-state.green {
  color: #18ff58;
}

.current-state.yellow {
  color: #ffe928;
}

.current-state.red {
  color: #ff202b;
}

.small-help {
  color: rgba(255, 255, 255, 0.82);
  font-size: 10px;
}

.phase-help {
  display: inline-flex;
  margin-top: 8px;
  padding: 4px 9px;
  border: 1px solid rgba(18, 200, 255, 0.52);
  border-radius: 999px;
  color: #12c8ff;
  font-size: 10px;
  font-weight: 650;
}

.remaining-label {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 24px;
  color: #ffffff;
  font-size: 14px;
  font-weight: 650;
  text-transform: uppercase;
}

.remaining-time {
  margin-top: 8px;
  font-size: 30px;
  font-weight: 800;
  line-height: 1;
}

.remaining-time.green {
  color: #18ff58;
}

.remaining-time.yellow {
  color: #ffe928;
}

.remaining-time.red {
  color: #ff202b;
}

.time-row {
  display: grid;
  grid-template-columns: 20px minmax(0, 1fr);
  align-items: center;
  gap: 16px;
  margin-top: 16px;
}

.time-title {
  color: #ffffff;
  font-size: 14px;
  font-weight: 650;
  text-transform: uppercase;
}

.slider-row {
  display: grid;
  grid-template-columns: 18px minmax(140px, 1fr) 28px 42px;
  align-items: center;
  gap: 10px;
  margin-left: 38px;
  color: #ffffff;
  font-size: 11px;
  font-weight: 650;
}

.value-box {
  display: grid;
  min-height: 32px;
  place-items: center;
  border: 1px solid #6947ff;
  border-radius: 5px;
  color: #ffffff;
  font-size: 10px;
  line-height: 1.1;
  text-align: center;
}

.mode-card,
.quick-card {
  margin-top: 18px;
}

.mode-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.mode-option,
.quick-action {
  border: 1px solid #6947ff;
  border-radius: 8px;
  background: rgba(35, 21, 84, 0.9);
  color: #ffffff;
  cursor: pointer;
  font: inherit;
}

.mode-option {
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr) 48px;
  align-items: center;
  gap: 12px;
  min-height: 58px;
  padding: 10px;
  text-align: left;
}

.mode-option.active {
  border-color: #8c70ff;
}

.mode-option strong,
.quick-action strong {
  display: block;
  font-size: 13px;
  font-weight: 650;
  line-height: 1.1;
  text-transform: uppercase;
}

.mode-option small,
.quick-action small {
  display: block;
  margin-top: 3px;
  color: rgba(255, 255, 255, 0.78);
  font-size: 9px;
  line-height: 1.15;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-top: 14px;
}

.quick-action {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 24px;
  align-items: center;
  gap: 8px;
  min-height: 48px;
  padding: 8px;
  text-align: left;
}

.green-action {
  border-color: #18ff58;
}

.red-action {
  border-color: #ff202b;
}

.yellow-action {
  border-color: #ffe928;
  color: #ffe928;
}

.reset-action {
  border-color: #7657ff;
  color: #8c70ff;
}

.traffic-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 90px;
  padding: 40px 30px 4px;
}

.action-button {
  min-height: 40px;
  border-radius: 6px !important;
  font-size: 13px;
  font-weight: 650;
  text-transform: uppercase;
}

@media (max-width: 720px) {
  .traffic-header {
    padding-left: 24px;
  }

  .traffic-grid,
  .mode-grid,
  .quick-grid,
  .traffic-actions {
    grid-template-columns: 1fr;
  }

  .traffic-actions {
    gap: 16px;
    padding: 24px 10px 4px;
  }
}

@media (max-width: 520px) {
  .traffic-content {
    padding-top: 22px;
  }

  .current-card,
  .timing-card,
  .mode-card,
  .quick-card {
    padding: 16px;
  }

  .slider-row {
    grid-template-columns: 16px minmax(0, 1fr) 26px;
    margin-left: 0;
  }

  .value-box {
    grid-column: 2 / -1;
    width: 58px;
    justify-self: end;
  }

  .mode-option {
    grid-template-columns: 34px minmax(0, 1fr) 44px;
  }
}
</style>
