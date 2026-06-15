<template>
  <v-main class="login-view">
    <section class="login-card">
      <div class="brand-panel">
        <img :src="trafficSimLogo" alt="TrafficSim" class="login-logo" />
      </div>

      <div class="form-panel">
        <div class="form-content">
          <h1>Hola</h1>
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

            <label class="field-label" for="password">Contrasena</label>
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

            <v-btn block height="44" type="submit" class="login-button">
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
  padding: 32px;
  overflow: hidden;
  background:
    linear-gradient(135deg, rgba(105, 71, 255, 0.08), transparent 38%),
    linear-gradient(315deg, rgba(18, 200, 255, 0.1), transparent 42%),
    #ffffff;
}

.login-view::before {
  position: absolute;
  inset: 0;
  content: "";
  opacity: 0.2;
  background-image:
    linear-gradient(rgba(105, 71, 255, 0.16) 1px, transparent 1px),
    linear-gradient(90deg, rgba(105, 71, 255, 0.16) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: linear-gradient(135deg, black, transparent 72%);
}

.login-card {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(420px, 1.12fr) minmax(340px, 0.88fr);
  width: min(1040px, 100%);
  min-height: 560px;
  overflow: hidden;
  border: 1px solid rgba(106, 75, 255, 0.18);
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 28px 90px rgba(23, 16, 59, 0.22);
}

.brand-panel {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 46px;
  background: #000000;
}

.brand-panel::after {
  position: absolute;
  inset: 24px;
  content: "";
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  pointer-events: none;
}

.login-logo {
  display: block;
  width: min(455px, 100%);
  height: auto;
  object-fit: contain;
  filter: drop-shadow(0 18px 28px rgba(111, 80, 255, 0.18));
}

.form-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 64px 72px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.04), transparent 34%),
    #1a1041;
}

.form-content {
  width: 100%;
  max-width: 318px;
}

.form-content h1 {
  margin: 0 0 6px;
  color: #ffffff;
  font-size: 30px;
  font-weight: 800;
  letter-spacing: 0;
}

.form-content p {
  margin: 0;
  color: rgba(255, 255, 255, 0.78);
  font-size: 13px;
}

.field-label {
  display: block;
  margin: 0 0 8px 4px;
  color: rgba(255, 255, 255, 0.92);
  font-size: 12px;
  font-weight: 700;
}

.login-input :deep(.v-field) {
  min-height: 44px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  color: #f8fafc;
  transition:
    background-color 150ms ease,
    box-shadow 150ms ease;
}

.login-input :deep(.v-field:hover) {
  background: rgba(255, 255, 255, 0.09);
}

.login-input :deep(.v-field--focused) {
  box-shadow: 0 0 0 3px rgba(18, 200, 255, 0.14);
}

.login-input :deep(.v-field__input) {
  min-height: 44px;
  padding-top: 0;
  padding-bottom: 0;
  font-size: 13px;
}

.login-input :deep(.v-field__outline) {
  color: rgba(255, 255, 255, 0.72);
}

.login-input :deep(.v-icon) {
  color: #ffffff;
  opacity: 0.92;
}

.login-button {
  min-height: 44px;
  border-radius: 12px;
  background: linear-gradient(90deg, #2f55ff, #6f50ff) !important;
  color: #ffffff !important;
  font-size: 14px;
  font-weight: 800;
  text-transform: none;
  box-shadow: 0 12px 26px rgba(77, 86, 255, 0.32);
  transition:
    transform 160ms ease,
    box-shadow 160ms ease,
    filter 160ms ease;
}

.login-button:hover {
  transform: translateY(-2px);
  filter: brightness(1.08);
  box-shadow: 0 18px 34px rgba(77, 86, 255, 0.44);
}

.login-button:active {
  transform: translateY(0);
  box-shadow: 0 10px 20px rgba(77, 86, 255, 0.3);
}

.register-link {
  display: block;
  margin: 18px auto 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: rgba(255, 255, 255, 0.78);
  font-size: 12px;
  font-weight: 800;
  text-decoration: none;
  cursor: pointer;
  transition: color 150ms ease;
}

.register-link:hover {
  color: #12c8ff;
}

@media (max-width: 860px) {
  .login-card {
    grid-template-columns: 1fr;
  }

  .brand-panel {
    padding: 44px 28px 34px;
  }

  .form-panel {
    padding: 38px 28px 46px;
  }
}

@media (max-width: 520px) {
  .login-view {
    padding: 18px;
  }

  .login-card {
    min-height: auto;
    border-radius: 14px;
  }

  .login-logo {
    width: min(320px, 100%);
  }
}
</style>
