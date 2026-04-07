import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  build: {
    // Output built files directly to the Django static folder
    outDir: '../BanglaCERT/static/react',
    emptyOutDir: true, // Clean the folder before build
    rollupOptions: {
      input: resolve(__dirname, 'src/main.jsx'),
      output: {
        entryFileNames: 'app.js',       // No hash for easy targeting in Django
        chunkFileNames: 'app-chunk.js', 
        assetFileNames: 'app.[ext]'     // CSS will output as app.css
      }
    }
  }
});
