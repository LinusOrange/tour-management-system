import { createRouter, createWebHashHistory } from 'vue-router'
// 1. 导入视图组件
import IngestView from '../views/IngestView.vue'
import PlannerView from '../views/Planner.vue'
import LoginView from '../views/Login.vue'
import RegisterView from '../views/Register.vue'
import AdminLogin from '../views/AdminLogin.vue' // 新增管理员登录

const routes = [
  { 
    path: '/login', 
    name: 'Login',
    component: LoginView,
    meta: { isPublic: true } 
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterView,
    meta: { isPublic: true } 
  },
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: AdminLogin,
    meta: { isPublic: true } // 管理员登录页也设为公开
  },
  { 
    path: '/', 
    name: 'Ingest',
    component: IngestView 
  },
  { 
    path: '/planner', 
    name: 'Planner',
    component: PlannerView 
  },
  { 
    path: '/library', 
    name: 'Library',
    component: () => import('../views/LibraryView.vue') 
  },
  {
    path: '/admin/dashboard',
    name: 'AdminDashboard',
    component: () => import('../views/AdminDashboard.vue'),
    // 修正：JS 中布尔值为 true (小写)
    meta: { requiresAdmin: true } 
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 2. 增强版全局路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  // 假设登录时将 is_admin 存入了 localStorage
  const isAdmin = localStorage.getItem('isAdmin') === 'true'
  
  const isPublicPage = to.matched.some(record => record.meta.isPublic)
  const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin)

  console.log(`[路由哨兵] 目标: ${to.path} | 公开: ${isPublicPage} | 管理员页: ${requiresAdmin}`)

  // 情况 A：访问公开页面（登录/注册）
  if (isPublicPage) {
    if (token) {
      // 已登录状态下，根据身份跳转到对应的首页
      return isAdmin ? next('/admin/dashboard') : next('/planner')
    }
    return next()
  }

  // 情况 B：访问受保护页面
  if (!token) {
    // 没登录：根据是否访问管理后台，重定向到不同的登录入口
    return requiresAdmin ? next('/admin/login') : next('/login')
  }

  // 情况 C：已登录，但访问管理员页面
  if (requiresAdmin && !isAdmin) {
    console.warn("普通用户尝试访问管理后台，已拦截")
    return next('/planner') // 强制踢回普通用户工作台
  }

  // 其他情况：放行
  next()
})

export default router