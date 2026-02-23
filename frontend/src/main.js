import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import axios from 'axios'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || `${window.location.protocol}//${window.location.hostname}:8000`

axios.defaults.baseURL = API_BASE_URL

// --- 1. 配置 Axios 请求拦截器 ---
// 每次发送请求时，自动从本地存储读取 Token 并放入 Header
axios.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}, error => {
  return Promise.reject(error)
})

// --- 2. 配置 Axios 响应拦截器 ---
// 处理 401 错误，防止在注册/登录页被反复踢出
axios.interceptors.response.use(
  response => response,
  error => {
    const currentPath = window.location.pathname
    const isPublicPage = ['/login', '/register', '/admin/login'].some(path => currentPath.startsWith(path))
    
    if (error.response && error.response.status === 401 && !isPublicPage) {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      // history 路由模式下跳转到登录页
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

const app = createApp(App)

// 3. 全局挂载 axios
app.config.globalProperties.$http = axios

app.use(router)
app.use(ElementPlus)
app.mount('#app')
