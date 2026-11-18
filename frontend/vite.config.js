import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // ตอนพัฒนา: คำขอที่ขึ้นต้นด้วย /api จะถูกส่งต่อไปที่ back-end (FastAPI) บนเครื่อง
    // หน้าเว็บกับ API จึงอยู่ที่อยู่เดียวกัน ไม่ต้องตั้งค่า CORS
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
