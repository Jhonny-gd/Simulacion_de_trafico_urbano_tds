<template>
  <v-app class="app-shell">
    <LoginView v-if="!isAuthenticated" @login="isAuthenticated = true" />
    <DashboardView v-else @logout="isAuthenticated = false" />
  </v-app>
</template>

<script setup>
import { ref } from 'vue'
import DashboardView from './views/DashboardView.vue'
import LoginView from './views/LoginView.vue'

const isAuthenticated = ref(false)
</script>
