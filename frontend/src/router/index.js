import { createRouter, createWebHistory } from 'vue-router'

// 路由定义
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue')
  },
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import('../views/AdminLogin.vue')
  },
  {
    path: '/',
    redirect: '/ingest'
  },
  {
    // AI 资源录入
    path: '/ingest',
    name: 'Ingest',
    component: () => import('../views/IngestView.vue'),
    meta: { requiresAuth: true }
  },
  {
    // 智能排产工作台
    path: '/planner',
    name: 'Planner',
    component: () => import('../views/Planner.vue'),
    meta: { requiresAuth: true }
  },
  {
    // 积木资产管理
    path: '/library',
    name: 'Library',
    component: () => import('../views/LibraryView.vue'),
    meta: { requiresAuth: true }
  },
  {
    // 🚀 新增：方案导出中心 (文案生成工作台)
    path: '/export',
    name: 'Export',
    component: () => import('../views/ExportWorkbench.vue'),
    meta: { requiresAuth: true }
  },
  {
    // 系统管理后台
    path: '/admin/dashboard',
    name: 'AdminDashboard',
    component: () => import('../views/AdminDashboard.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// --- 🔐 全局路由守卫 (身份验证与权限控制) ---
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const isRealAdmin = localStorage.getItem('realAdminRole') === 'admin'

  // 1. 检查是否需要登录权限
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } 
  // 2. 检查是否需要管理员权限
  else if (to.meta.requiresAdmin && !isRealAdmin) {
    next('/ingest') // 普通用户尝试进入后台，重定向回录入台
  } 
  else {
    next()
  }
})

export default router