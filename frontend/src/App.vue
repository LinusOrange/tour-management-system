<template>
  <el-container class="main-layout">
    <el-header v-if="!['/login', '/register', '/admin/login'].includes($route.path)" class="nav-header">
      <div class="logo">研学原子积木系统</div>
      
      <el-menu mode="horizontal" router :default-active="$route.path" class="menu-nav">
        <template v-if="!isAdmin">
          <el-menu-item index="/ingest">AI 资源录入</el-menu-item>
          <el-menu-item index="/planner">智能排产工作台</el-menu-item>
          <el-menu-item index="/library">积木资产管理</el-menu-item>
        </template>
        
        <template v-else>
          <el-menu-item index="/admin/dashboard">
            <el-icon><Setting /></el-icon> 系统管理后台
          </el-menu-item>
          <el-menu-item index="/library">全局资源审计</el-menu-item>
        </template>
      </el-menu>

      <div class="user-info">
        <el-dropdown @command="handleCommand">
          <span class="el-dropdown-link">
            <el-tag v-if="isAdmin" size="small" type="danger" class="mr-2">管理员模式</el-tag>
            <el-avatar :size="24" class="mr-2" src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png" />
            {{ username }}
            <el-icon class="el-icon--right"><arrow-down /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-if="isAdmin" command="goUserView">切换至用户视图</el-dropdown-item>
              
              <el-dropdown-item v-if="!isAdmin && isRealAdmin" command="goAdminView">返回管理后台</el-dropdown-item>
              
              <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <el-main :class="{ 'no-padding': ['/login', '/register', '/admin/login'].includes($route.path) }">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowDown, Setting } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const username = ref('未登录')
const isAdmin = ref(false)         // 当前 UI 呈现模式
const isRealAdmin = ref(false)     // 账户的真实管理员属性

// 状态同步函数
const syncUserStatus = () => {
  username.value = localStorage.getItem('username') || '用户'
  // 读取当前 UI 状态
  isAdmin.value = localStorage.getItem('isAdmin') === 'true'
  // 读取真实身份（建议登录时额外存一个标志位 realAdminRole: 'admin'）
  isRealAdmin.value = localStorage.getItem('realAdminRole') === 'admin'
}

onMounted(syncUserStatus)
watch(() => route.path, syncUserStatus)

const handleCommand = (command) => {
  if (command === 'logout') {
    localStorage.clear() // 彻底清理
    ElMessage.success('已安全退出系统')
    router.push('/login')
  } 
  else if (command === 'goUserView') {
    // 1. 修改本地状态标志位
    localStorage.setItem('isAdmin', 'false')
    // 2. 立即触发本地变量更新，让 Header 重新渲染
    syncUserStatus()
    // 3. 跳转
    ElMessage.info('已进入普通用户预览模式')
    router.push('/planner')
  }
  else if (command === 'goAdminView') {
    // 切换回管理模式
    localStorage.setItem('isAdmin', 'true')
    syncUserStatus()
    router.push('/admin/dashboard')
  }
}
</script>

<style scoped>
/* 样式保持不变 */
.nav-header { display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #dcdfe6; background: #fff; padding: 0 20px; }
.logo { font-weight: bold; color: #409EFF; margin-right: 40px; flex-shrink: 0; }
.menu-nav { border-bottom: none; flex-grow: 1; }
.main-layout { background: #f5f7fa; min-height: 100vh; }
.user-info { display: flex; align-items: center; margin-left: 20px; cursor: pointer; }
.el-dropdown-link { display: flex; align-items: center; color: #606266; font-size: 14px; }
.no-padding { padding: 0 !important; }
.mr-2 { margin-right: 8px; }
</style>