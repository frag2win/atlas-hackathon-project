// File: frontend/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import tailwindcss from '@tailwindcss/postcss' // Import the tailwindcss plugin

export default defineConfig({
  plugins: [react()],
  // Add this 'css' object to configure PostCSS
  css: {
    postcss: {
      plugins: [tailwindcss],
    },
  },
})