import { defineConfig } from 'vite';

export default defineConfig({
    root: 'static',
    build: {
        outDir: 'dist',
        emptyOutDir: true,
        chunkSizeWarningLimit: 600,  // Three.js is ~530KB, can't be split further
        rollupOptions: {
            output: {
                manualChunks: {
                    three: ['three'],
                },
            },
        },
    },
    server: {
        proxy: {
            '/ws': {
                target: 'http://localhost:8766',
                ws: true,
            },
        },
    },
});
