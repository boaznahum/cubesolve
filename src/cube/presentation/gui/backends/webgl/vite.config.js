import { defineConfig } from 'vite';

export default defineConfig({
    root: 'static',
    build: {
        outDir: 'dist',
        emptyOutDir: true,
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
