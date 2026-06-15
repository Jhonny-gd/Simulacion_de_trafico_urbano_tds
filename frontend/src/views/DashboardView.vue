<template>
  <AppSidebar :active-section="activeSection" @select-section="selectSection" />

  <AppTopbar
    :simulation-state="simulationState"
    :api-online="apiOnline"
    @start="runControl('start')"
    @pause="runControl('pause')"
    @reset="runControl('reset')"
    @logout="$emit('logout')"
  />

  <v-main class="dashboard-main">
    <v-container fluid class="pa-6 pa-md-8">
      <v-row class="mb-5">
        <v-col cols="12" sm="6" lg="3">
          <MetricCard
            label="Vehiculos"
            :value="config.conteo_vehiculos"
            detail="Nodos activos detectados"
            icon="mdi-car-multiple"
            color="primary"
          />
        </v-col>
        <v-col cols="12" sm="6" lg="3">
          <MetricCard
            label="Tiempo"
            :value="simulationTimeLabel"
            detail="Tiempo real de Webots"
            icon="mdi-timer-outline"
            color="accent"
          />
        </v-col>
        <v-col cols="12" sm="6" lg="3">
          <MetricCard
            label="Congestion"
            :value="`${config.nivel_congestion}%`"
            detail="Indice operacional"
            icon="mdi-alert-circle-outline"
            color="error"
          />
        </v-col>
        <v-col cols="12" sm="6" lg="3">
          <MetricCard
            label="Flujo"
            :value="config.flujo_vehicular"
            detail="Vehiculos por velocidad"
            icon="mdi-transit-connection"
            color="secondary"
          />
        </v-col>
      </v-row>

      <v-row class="mb-5">
        <v-col cols="12" lg="5">
          <v-card class="surface-card live-card pa-5 h-100">
            <div class="d-flex align-center justify-space-between mb-5">
              <div>
                <div class="panel-kicker">Operacion en vivo</div>
                <div class="text-h6 font-weight-medium">Estado de la simulacion</div>
              </div>
              <v-chip :color="webotsOnline ? 'success' : 'error'" variant="flat" size="small">
                {{ webotsOnline ? 'Webots online' : 'Webots desconectado' }}
              </v-chip>
            </div>

            <div class="live-stat-grid">
              <div class="live-stat">
                <v-icon icon="mdi-car-multiple" color="primary" />
                <span>Vehiculos activos</span>
                <strong>{{ config.conteo_vehiculos }}</strong>
              </div>
              <div class="live-stat">
                <v-icon icon="mdi-speedometer" color="secondary" />
                <span>Velocidad promedio</span>
                <strong>{{ config.velocidad_promedio }} m/s</strong>
              </div>
              <div class="live-stat">
                <v-icon icon="mdi-map-marker-distance" color="accent" />
                <span>Densidad</span>
                <strong>{{ config.densidad_trafico }}</strong>
              </div>
            </div>
          </v-card>
        </v-col>

        <v-col cols="12" lg="7">
          <v-card class="surface-card traffic-live-card pa-5 h-100">
            <div class="d-flex align-center justify-space-between mb-5">
              <div>
                <div class="panel-kicker">Semaforo por zona</div>
                <div class="text-h6 font-weight-medium">{{ config.zona_semaforo }}</div>
              </div>
              <v-chip :color="trafficStateColor" variant="flat" size="small">
                {{ trafficStateLabel }}
              </v-chip>
            </div>

            <div class="traffic-live-grid">
              <div class="traffic-current">
                <div class="traffic-current-label">Estado actual</div>
                <div :class="['traffic-current-state', config.estado_semaforo]">
                  {{ trafficStateLabel }}
                </div>
                <div class="muted-text text-caption">
                  {{ config.semaforos_detectados }} semaforos detectados
                </div>
                <div class="traffic-phase-pill">
                  Fase {{ trafficPhaseLabel }}
                </div>
              </div>

              <div class="traffic-timers">
                <div class="timer-line">
                  <span class="timer-dot red" />
                  <span>Rojo</span>
                  <strong>{{ formatSeconds(config.tiempo_luz_roja) }}</strong>
                </div>
                <div class="timer-line">
                  <span class="timer-dot green" />
                  <span>Verde</span>
                  <strong>{{ formatSeconds(config.tiempo_luz_verde) }}</strong>
                </div>
                <div class="timer-line remaining">
                  <v-icon icon="mdi-timer-sand" size="18" color="secondary" />
                  <span>Restante</span>
                  <strong :class="['remaining-dashboard-time', config.estado_semaforo]">
                    {{ formatSeconds(config.tiempo_restante_semaforo) }}
                  </strong>
                </div>
                <div class="timer-line">
                  <v-icon icon="mdi-axis-arrow" size="18" color="primary" />
                  <span>Sentido activo</span>
                  <strong>{{ trafficPhaseLabel }}</strong>
                </div>
                <div class="timer-line">
                  <span class="timer-dot red" />
                  <span>Sentido en rojo</span>
                  <strong>{{ trafficBlockedPhaseLabel }}</strong>
                </div>
              </div>
            </div>
          </v-card>
        </v-col>
      </v-row>

      <v-row>
        <v-col cols="12">
          <WebotsStreamPanel />
        </v-col>
      </v-row>

      <v-alert
        v-if="errorMessage"
        type="warning"
        variant="tonal"
        density="compact"
        class="mt-5"
      >
        {{ errorMessage }}
      </v-alert>

      <v-alert
        v-else-if="apiOnline && !webotsOnline"
        type="warning"
        variant="tonal"
        density="compact"
        class="mt-5"
      >
        Webots desconectado
      </v-alert>
    </v-container>

    <v-slide-x-reverse-transition>
      <aside
        v-if="activePanel"
        :class="[
          'floating-panel-dock',
          {
            'floating-panel-dock--control': activePanel === 'control',
            'floating-panel-dock--vehicle': activePanel === 'vehicles',
            'floating-panel-dock--traffic': activePanel === 'trafficLights',
          },
        ]"
      >
        <div
          v-if="!['control', 'vehicles', 'trafficLights'].includes(activePanel)"
          class="d-flex align-center justify-space-between mb-3"
        >
          <div>
            <div class="text-subtitle-2 font-weight-bold">{{ activePanelTitle }}</div>
            <div class="text-caption muted-text">Panel flotante</div>
          </div>
          <v-btn icon="mdi-close" variant="text" density="comfortable" @click="activeSection = 'dashboard'" />
        </div>

        <VehicleControlPanel
          v-if="activePanel === 'control'"
          :config="config"
          @update-config="updateConfig"
          @close="activeSection = 'dashboard'"
        />
        <VehicleFunctionsPanel
          v-if="activePanel === 'vehicles'"
          :config="config"
          @update-config="updateConfig"
          @close="activeSection = 'dashboard'"
        />
        <TrafficLightControlPanel
          v-if="activePanel === 'trafficLights'"
          :config="config"
          @update-config="updateConfig"
          @close="activeSection = 'dashboard'"
        />
        <MonitoringPanel
          v-if="activePanel === 'monitoring'"
          :config="config"
          :simulation-state="simulationState"
        />
      </aside>
    </v-slide-x-reverse-transition>
  </v-main>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import AppSidebar from '../components/layout/AppSidebar.vue'
import AppTopbar from '../components/layout/AppTopbar.vue'
import MetricCard from '../components/dashboard/MetricCard.vue'
import MonitoringPanel from '../components/simulation/MonitoringPanel.vue'
import TrafficLightControlPanel from '../components/simulation/TrafficLightControlPanel.vue'
import VehicleControlPanel from '../components/simulation/VehicleControlPanel.vue'
import VehicleFunctionsPanel from '../components/simulation/VehicleFunctionsPanel.vue'
import WebotsStreamPanel from '../components/simulation/WebotsStreamPanel.vue'
import { simulationService } from '../services/simulationService'
import { showErrorAlert, showSuccessToast } from '../utils/alerts'

defineEmits(['logout'])

const activeSection = ref('dashboard')
const simulationState = ref('stopped')
const apiOnline = ref(false)
const webotsOnline = ref(false)
const errorMessage = ref('')
let pollingId = null

const config = reactive({
  conteo_vehiculos: 0,
  vehiculos_activos: 0,
  densidad_trafico: 0,
  velocidad_promedio: 0,
  flujo_vehicular: 0,
  nivel_congestion: 0,
  tiempo_simulacion: 0,
  estado_semaforo: 'red',
  fase_semaforo: 'north_south',
  tiempo_luz_verde: 30,
  tiempo_luz_roja: 30,
  tiempo_restante_semaforo: 30,
  semaforos_detectados: 0,
  zona_semaforo: 'Interseccion central',
  modo_automatico_semaforo: true,
  control_manual_semaforo: null,
  tipo_vehiculo: 'sedan',
  direccion_vehiculo: 'straight',
  cambio_velocidad_individual: 0,
  vehiculo_seleccionado: 'veh_01',
  velocidad_global: 70,
  velocidad_maxima_coche: 120,
  velocidad_maxima_camion: 90,
  velocidad_maxima_autobus: 100,
  velocidad_maxima_moto: 120,
  senales_vehiculo: {
    luces: false,
    direccional: false,
    bocina: false,
    emergencia: false,
  },
  control_rutas: 'principal',
})

const panelTitles = {
  control: 'Control',
  vehicles: 'Vehiculos',
  trafficLights: 'Semaforos',
  monitoring: 'Monitoreo',
}

const floatingPanelSections = ['control', 'vehicles', 'trafficLights', 'monitoring']

const activePanel = computed(() => (
  floatingPanelSections.includes(activeSection.value) ? activeSection.value : null
))

const activePanelTitle = computed(() => panelTitles[activePanel.value] ?? '')
const simulationTimeLabel = computed(() => formatSeconds(config.tiempo_simulacion))
const trafficStateLabel = computed(() => {
  const labels = {
    green: 'Verde',
    yellow: 'Amarillo',
    red: 'Rojo',
  }

  return labels[config.estado_semaforo] ?? 'Rojo'
})

const trafficStateColor = computed(() => {
  if (config.estado_semaforo === 'green') return 'success'
  if (config.estado_semaforo === 'yellow') return 'warning'
  return 'error'
})

const trafficPhaseLabel = computed(() => {
  const labels = {
    north_south: 'Norte-Sur',
    east_west: 'Este-Oeste',
  }

  return labels[config.fase_semaforo] ?? 'Norte-Sur'
})

const trafficBlockedPhaseLabel = computed(() => (
  config.fase_semaforo === 'north_south' ? 'Este-Oeste' : 'Norte-Sur'
))

function selectSection(section) {
  activeSection.value = section
}

function formatSeconds(value) {
  const totalSeconds = Math.max(0, Math.floor(Number(value) || 0))
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = String(totalSeconds % 60).padStart(2, '0')
  return `${minutes}:${seconds}`
}

async function loadSimulation() {
  try {
    const status = await simulationService.getStatus()
    const nextConfig = normalizeStatusPayload(status)

    Object.assign(config, nextConfig)
    simulationState.value = status.estado_simulacion ?? status.estado ?? 'stopped'
    apiOnline.value = true
    webotsOnline.value = Boolean(status.webots_conectado)
    errorMessage.value = ''
  } catch (error) {
    apiOnline.value = false
    webotsOnline.value = false
    errorMessage.value = 'No se pudo conectar con FastAPI. La interfaz conserva los ultimos datos disponibles.'
  }
}

function normalizeStatusPayload(status) {
  const configPayload = status.configuracion ?? {}

  return {
    ...configPayload,
    vehiculos_activos: status.vehiculos_activos ?? status.conteo_vehiculos ?? configPayload.conteo_vehiculos ?? 0,
    conteo_vehiculos: status.conteo_vehiculos ?? status.vehiculos_activos ?? configPayload.conteo_vehiculos ?? 0,
    densidad_trafico: status.densidad_trafico ?? configPayload.densidad_trafico ?? 0,
    velocidad_promedio: status.velocidad_promedio ?? configPayload.velocidad_promedio ?? 0,
    flujo_vehicular: status.flujo_vehicular ?? configPayload.flujo_vehicular ?? 0,
    nivel_congestion: status.nivel_congestion ?? configPayload.nivel_congestion ?? 0,
    tiempo_simulacion: status.tiempo_simulacion ?? configPayload.tiempo_simulacion ?? 0,
    estado_semaforo: status.estado_semaforo ?? configPayload.estado_semaforo ?? 'red',
    fase_semaforo: status.fase_semaforo ?? configPayload.fase_semaforo ?? 'north_south',
    tiempo_restante_semaforo: status.tiempo_restante_semaforo ?? configPayload.tiempo_restante_semaforo ?? 0,
    semaforos_detectados: status.semaforos_detectados ?? configPayload.semaforos_detectados ?? 0,
    zona_semaforo: status.zona_semaforo ?? configPayload.zona_semaforo ?? 'Interseccion central',
  }
}

async function updateConfig(nextConfig) {
  try {
    const savedConfig = await simulationService.updateConfig(nextConfig)
    Object.assign(config, savedConfig)
    apiOnline.value = true
    errorMessage.value = ''
    activeSection.value = 'dashboard'
    showSuccessToast('Cambios aplicados correctamente')
  } catch (error) {
    apiOnline.value = false
    errorMessage.value = 'No se pudo guardar la configuracion en el backend.'
    showErrorAlert('No se aplicaron los cambios', errorMessage.value)
  }
}

async function runControl(action) {
  try {
    const response = await simulationService[action]()
    simulationState.value = response.estado_simulacion ?? simulationState.value
    apiOnline.value = true
    errorMessage.value = ''
    await loadSimulation()
  } catch (error) {
    apiOnline.value = false
    errorMessage.value = 'No se pudo ejecutar el comando de control.'
  }
}

onMounted(() => {
  loadSimulation()
  pollingId = window.setInterval(loadSimulation, 1000)
})

onBeforeUnmount(() => {
  if (pollingId) window.clearInterval(pollingId)
})
</script>

<style scoped>
.panel-kicker {
  margin-bottom: 4px;
  color: #12c8ff;
  font-size: 12px;
  font-weight: 650;
  text-transform: uppercase;
}

.live-card,
.traffic-live-card {
  border-color: rgba(105, 71, 255, 0.7) !important;
  background:
    linear-gradient(135deg, rgba(111, 80, 255, 0.13), transparent 48%),
    #25165c !important;
}

.live-stat-grid {
  display: grid;
  gap: 12px;
}

.live-stat {
  display: grid;
  grid-template-columns: 30px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  min-height: 48px;
  padding: 10px 12px;
  border: 1px solid rgba(105, 71, 255, 0.7);
  border-radius: 8px;
  background: rgba(13, 8, 40, 0.34);
}

.live-stat span,
.timer-line span {
  color: rgba(255, 255, 255, 0.72);
  font-size: 12px;
}

.live-stat strong,
.timer-line strong {
  color: #ffffff;
  font-size: 14px;
  font-weight: 650;
  white-space: nowrap;
}

.traffic-live-grid {
  display: grid;
  grid-template-columns: minmax(160px, 0.85fr) minmax(240px, 1.15fr);
  gap: 18px;
}

.traffic-current,
.traffic-timers {
  min-height: 150px;
  padding: 16px;
  border: 1px solid rgba(105, 71, 255, 0.7);
  border-radius: 8px;
  background: rgba(13, 8, 40, 0.34);
}

.traffic-current-label {
  color: rgba(255, 255, 255, 0.72);
  font-size: 12px;
  text-transform: uppercase;
}

.traffic-current-state {
  margin: 14px 0 6px;
  font-size: 34px;
  font-weight: 750;
  line-height: 1;
  text-transform: uppercase;
}

.traffic-current-state.green,
.remaining-dashboard-time.green {
  color: #18ff58;
}

.traffic-current-state.yellow,
.remaining-dashboard-time.yellow {
  color: #ffe928;
}

.traffic-current-state.red,
.remaining-dashboard-time.red {
  color: #ff244f;
}

.traffic-phase-pill {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  margin-top: 12px;
  padding: 0 10px;
  border: 1px solid rgba(18, 200, 255, 0.5);
  border-radius: 999px;
  color: #12c8ff;
  font-size: 11px;
  font-weight: 650;
}

.traffic-timers {
  display: grid;
  align-content: center;
  gap: 12px;
}

.timer-line {
  display: grid;
  grid-template-columns: 18px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  min-height: 34px;
}

.timer-line.remaining {
  grid-template-columns: 18px minmax(0, 1fr) auto;
  padding-top: 8px;
  border-top: 1px solid rgba(173, 165, 255, 0.22);
}

.timer-dot {
  width: 12px;
  height: 12px;
  border-radius: 999px;
}

.timer-dot.red {
  background: #ff244f;
}

.timer-dot.green {
  background: #18ff58;
}

@media (max-width: 959px) {
  .traffic-live-grid {
    grid-template-columns: 1fr;
  }
}
</style>
