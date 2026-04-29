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
        <v-col cols="12" sm="6" lg="3">
          <MetricCard
            label="Semaforo"
            :value="config.estado_semaforo"
            detail="Estado actual del ciclo"
            icon="mdi-traffic-light"
            :color="config.estado_semaforo === 'green' ? 'success' : 'error'"
          />
        </v-col>
      </v-row>

      <v-row>
        <v-col cols="12">
          <v-card class="surface-card pa-5 position-relative overflow-hidden">
            <div class="webots-preview d-flex align-center justify-center position-relative">
              <div class="preview-grid" />
              <div class="position-relative text-center">
                <v-icon icon="mdi-video-input-component" size="52" color="secondary" class="mb-3" />
                <div class="text-h5 font-weight-bold">Vista de simulacion Webots</div>
                <div class="text-body-2 muted-text mt-2">Area reservada para captura, stream o video</div>
              </div>
            </div>
          </v-card>
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
    </v-container>

    <v-slide-x-reverse-transition>
      <aside v-if="activePanel" class="floating-panel-dock">
        <div class="d-flex align-center justify-space-between mb-3">
          <div>
            <div class="text-subtitle-2 font-weight-bold">{{ activePanelTitle }}</div>
            <div class="text-caption muted-text">Panel flotante</div>
          </div>
          <v-btn icon="mdi-close" variant="text" density="comfortable" @click="activeSection = 'dashboard'" />
        </div>

        <VehicleControlPanel
          v-if="activePanel === 'vehicles'"
          :config="config"
          @update-config="updateConfig"
        />
        <TrafficLightControlPanel
          v-if="activePanel === 'trafficLights'"
          :config="config"
          @update-config="updateConfig"
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
import { simulationService } from '../services/simulationService'

defineEmits(['logout'])

const activeSection = ref('dashboard')
const simulationState = ref('stopped')
const apiOnline = ref(false)
const errorMessage = ref('')
let pollingId = null

const config = reactive({
  conteo_vehiculos: 0,
  densidad_trafico: 0,
  velocidad_promedio: 0,
  flujo_vehicular: 0,
  nivel_congestion: 0,
  estado_semaforo: 'red',
  tiempo_luz_verde: 30,
  tiempo_luz_roja: 30,
  modo_automatico_semaforo: true,
  control_manual_semaforo: null,
  tipo_vehiculo: 'car',
  direccion_vehiculo: 'straight',
  cambio_velocidad_individual: 0,
  senales_vehiculo: 'none',
  control_rutas: 'default',
})

const panelTitles = {
  vehicles: 'Vehiculos',
  trafficLights: 'Semaforos',
  monitoring: 'Monitoreo',
}

const activePanel = computed(() => (
  activeSection.value === 'dashboard' ? null : activeSection.value
))

const activePanelTitle = computed(() => panelTitles[activePanel.value] ?? '')

function selectSection(section) {
  activeSection.value = section
}

async function loadSimulation() {
  try {
    const status = await simulationService.getStatus()
    const nextConfig = status.configuracion ?? await simulationService.getConfig()

    Object.assign(config, nextConfig)
    simulationState.value = status.estado_simulacion ?? 'stopped'
    apiOnline.value = true
    errorMessage.value = ''
  } catch (error) {
    apiOnline.value = false
    errorMessage.value = 'No se pudo conectar con FastAPI. La interfaz conserva los ultimos datos disponibles.'
  }
}

async function updateConfig(nextConfig) {
  try {
    const savedConfig = await simulationService.updateConfig(nextConfig)
    Object.assign(config, savedConfig)
    apiOnline.value = true
    errorMessage.value = ''
  } catch (error) {
    apiOnline.value = false
    errorMessage.value = 'No se pudo guardar la configuracion en el backend.'
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
  pollingId = window.setInterval(loadSimulation, 2000)
})

onBeforeUnmount(() => {
  if (pollingId) window.clearInterval(pollingId)
})
</script>
