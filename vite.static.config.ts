import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
import {resolve} from 'node:path';
export default defineConfig({root:resolve(import.meta.dirname,'static'),base:process.env.PAGES_BASE||'/',publicDir:resolve(import.meta.dirname,'public'),plugins:[react()],build:{outDir:resolve(import.meta.dirname,'dist-pages'),emptyOutDir:true},resolve:{alias:{'@':import.meta.dirname}}});
