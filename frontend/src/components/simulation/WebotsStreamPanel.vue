<template>
  <v-card class="surface-card pa-5 position-relative overflow-hidden">
    <div class="webots-stream">
      <template v-if="streamUrl">
        <img
          v-if="streamKind === 'image'"
          :src="streamUrl"
          alt="Stream en vivo de Webots"
          class="stream-media"
        />
        <video
          v-else-if="streamKind === 'video'"
          :src="streamUrl"
          class="stream-media"
          autoplay
          muted
          playsinline
          controls
        />
        <iframe
          v-else
          :src="streamUrl"
          class="stream-media"
          title="Stream en vivo de Webots"
          allow="autoplay; fullscreen"
        />
      </template>

      <div v-else class="stream-placeholder">
        <div class="preview-grid" />
        <div class="position-relative text-center">
          <v-icon icon="mdi-video-input-component" size="52" color="secondary" class="mb-3" />
          <div class="text-h5 font-weight-bold">Vista de simulacion Webots</div>
          <div class="text-body-2 muted-text mt-2">
            Esperando imagen en vivo desde Webots
          </div>
        </div>
      </div>
    </div>
  </v-card>
</template>

<script setup>
import { computed } from 'vue'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
const streamUrl = import.meta.env.VITE_WEBOTS_STREAM_URL || `${apiBaseUrl}/simulation/stream.mjpg`

const streamKind = computed(() => {
  const url = streamUrl.toLowerCase()

  if (/\.(mjpeg|mjpg|jpg|jpeg|png|gif)(\?|$)/.test(url)) return 'image'
  if (/\.(mp4|webm|ogg|m3u8)(\?|$)/.test(url)) return 'video'

  return 'page'
})
</script>

<style scoped>
.webots-stream {
  position: relative;
  min-height: 420px;
  border: 1px dashed rgba(18, 200, 255, 0.42);
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(111, 80, 255, 0.22), rgba(18, 200, 255, 0.1)),
    #1a1041;
  overflow: hidden;
}

.stream-media {
  display: block;
  width: 100%;
  height: 100%;
  min-height: 420px;
  border: 0;
  object-fit: cover;
  image-rendering: auto;
  background: #050312;
}

.stream-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 1279px) {
  .webots-stream,
  .stream-media {
    min-height: 300px;
  }
}
</style>
