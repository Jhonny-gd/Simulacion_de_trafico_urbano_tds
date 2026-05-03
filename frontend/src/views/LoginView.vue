<template>
  <v-main class="login-view">
    <section class="login-card">
      <div class="brand-panel">
        <img :src="trafficSimLogo" alt="TrafficSim" class="login-logo" />
      </div>

      <div class="form-panel">
        <div class="form-content">
          <h1>¡Hola!</h1>
          <p>Inicia sesion para empezar</p>

          <v-form class="mt-8" @submit.prevent="$emit('login')">
            <label class="field-label" for="username">Usuario</label>
            <v-text-field
              id="username"
              v-model="username"
              variant="outlined"
              density="compact"
              bg-color="transparent"
              hide-details
              class="login-input mb-5"
              append-inner-icon="mdi-account-circle"
            />

            <label class="field-label" for="password">Contraseña</label>
            <v-text-field
              id="password"
              v-model="password"
              type="password"
              variant="outlined"
              density="compact"
              bg-color="transparent"
              hide-details
              class="login-input mb-10"
              append-inner-icon="mdi-lock-outline"
            />

            <v-btn block height="38" type="submit" class="login-button">
              Iniciar
            </v-btn>
          </v-form>

          <button class="register-link" type="button">Registrarse</button>
        </div>
      </div>
    </section>
  </v-main>
</template>

<script setup>
import { ref } from 'vue'
import trafficSimLogo from '../assets/trafficsim-login.png'

defineEmits(['login'])

const username = ref('admin')
const password = ref('admin123')
</script>

<style scoped>
.login-view {
  position: relative;
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  overflow: hidden;
  background:
    radial-gradient(circle at 14% 18%, rgba(111, 80, 255, 0.28), transparent 32%),
    radial-gradient(circle at 88% 78%, rgba(18, 200, 255, 0.14), transparent 30%),
    linear-gradient(135deg, rgba(105, 71, 255, 0.08), transparent 46%),
    #ffffff;
}

.login-view::before {
  position: absolute;
  inset: 0;
  content: "";
  opacity: 0.28;
  background-image:
    linear-gradient(rgba(105, 71, 255, 0.12) 1px, transparent 1px),
    linear-gradient(90deg, rgba(105, 71, 255, 0.12) 1px, transparent 1px);
  background-size: 44px 44px;
}

.login-card {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 1.15fr 0.95fr;
  width: min(980px, 100%);
  min-height: 532px;
  overflow: hidden;
  border: 1px solid rgba(173, 165, 255, 0.3);
  border-radius: 8px;
  background: linear-gradient(90deg, #000000 0 54.8%, #1a1041 54.8% 100%);
  box-shadow: none;
}

.brand-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 34px;
  background: #000000;
}

.login-logo {
  display: block;
  width: min(430px, 100%);
  height: auto;
  object-fit: contain;
}

.form-panel {
  display: flex;
  align-items: center;
  padding: 58px 84px;
  background: #1a1041;
}

.form-content {
  width: 100%;
  max-width: 290px;
}

.form-content h1 {
  margin: 0 0 4px;
  font-size: 24px;
  font-weight: 800;
  letter-spacing: 0;
  color: #ffffff;
}

.form-content p {
  margin: 0;
  font-size: 12px;
  color: #ffffff;
}

.field-label {
  display: block;
  margin: 0 0 7px 8px;
  font-size: 11px;
  font-weight: 700;
  color: #ffffff;
}

.login-input :deep(.v-field) {
  min-height: 38px;
  border-radius: 14px;
  color: #f8fafc;
}

.login-input :deep(.v-field__input) {
  min-height: 38px;
  padding-top: 0;
  padding-bottom: 0;
  font-size: 12px;
}

.login-input :deep(.v-field__outline) {
  color: rgba(255, 255, 255, 0.86);
}

.login-input :deep(.v-icon) {
  color: #ffffff;
  opacity: 0.92;
}

.login-button {
  border-radius: 12px;
  background: linear-gradient(90deg, #2f55ff, #6f50ff) !important;
  color: #ffffff !important;
  font-size: 14px;
  font-weight: 800;
  text-transform: none;
  box-shadow: none;
}

.register-link {
  display: block;
  margin: 14px auto 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: #ffffff;
  font-size: 11px;
  font-weight: 800;
  text-decoration: underline;
  cursor: pointer;
}

@media (max-width: 860px) {
  .login-card {
    grid-template-columns: 1fr;
    background: linear-gradient(180deg, #000000 0 48%, #1a1041 48% 100%);
  }

  .brand-panel {
    padding: 38px 24px 28px;
  }

  .form-panel {
    justify-content: center;
    padding: 34px 24px 42px;
  }
}

@media (max-width: 520px) {
  .login-logo {
    width: min(320px, 100%);
  }
}
</style>
