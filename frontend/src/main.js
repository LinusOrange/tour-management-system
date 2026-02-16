import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import axios from 'axios'

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
    // 更加稳健的公开页检测逻辑
    const currentPath = window.location.hash.replace('#', '');
    const isPublicPage = ['/login', '/register'].some(path => currentPath.startsWith(path));
    
    if (error.response && error.response.status === 401 && !isPublicPage) {
      localStorage.removeItem('token');
      localStorage.removeItem('username');
      // 仅在非公开页面时强制跳转
      window.location.href = '/#/login'; 
    }
    return Promise.reject(error);
  }
);

// --- 3. 配置路由守卫 (Navigation Guard) ---
// 核心修复：基于路由 meta 属性进行判断，而不是死记硬背路径
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  
  // 使用 matched.some 确保即使是嵌套路由也能正确获取 isPublic 状态
  const isPublic = to.matched.some(record => record.meta.isPublic)

  if (!isPublic && !token) {
    // 拦截：非公开页面且无 Token，强制去登录
    next('/login')
  } else {
    // 放行：公开页面（含 /login 和 /register）或已登录
    next()
  }
})

const app = createApp(App)

// 4. 全局挂载 axios
app.config.globalProperties.$http = axios

app.use(router)
app.use(ElementPlus)
app.mount('#app')