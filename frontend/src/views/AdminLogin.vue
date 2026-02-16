<template>
  <div class="admin-login-page">
    <div class="bg-glow"></div>
    
    <div class="admin-login-card">
      <div class="header">
        <el-icon :size="40" color="#409EFF"><Setting /></el-icon>
        <h2>系统管理后台</h2>
        <p>研学原子积木系统 - 核心管理入口</p>
      </div>

      <el-form :model="adminForm" :rules="rules" ref="formRef" label-position="top">
        <el-form-item label="管理员账号" prop="username">
          <el-input 
            v-model="adminForm.username" 
            placeholder="请输入管理员用户名"
            :prefix-icon="User"
            size="large"
          />
        </el-form-item>

        <el-form-item label="管理密码" prop="password">
          <el-input 
            v-model="adminForm.password" 
            type="password" 
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
            size="large"
            @keyup.enter="handleAdminLogin"
          />
        </el-form-item>

        <el-button 
          type="primary" 
          class="login-btn" 
          :loading="loading" 
          @click="handleAdminLogin"
        >
          {{ loading ? '正在校验指纹...' : '验证并进入后台' }}
        </el-button>

        <div class="footer-links">
          <el-button link type="primary" @click="$router.push('/login')">返回普通用户登录</el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { User, Lock, Setting } from '@element-plus/icons-vue'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const adminForm = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '管理账号必填', trigger: 'blur' }],
  password: [{ required: true, message: '管理密码必填', trigger: 'blur' }]
}

const handleAdminLogin = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      // 1. 调用登录接口
      const res = await axios.post('http://123.206.212.218:8000/api/v1/auth/login', adminForm)
      
      // 2. 存储身份标识
      localStorage.setItem('token', res.data.access_token)
      localStorage.setItem('username', adminForm.username)
      
      // 核心修复：手动存入管理员标记，解决路由拦截问题
      // 注意：必须存储为字符串 'true'，因为路由守卫读取的是字符串比较
      localStorage.setItem('isAdmin', 'true')
      
      ElMessage.success({
        message: '管理员身份核验成功，正在进入系统...',
        type: 'success',
        duration: 1500
      })
      
      // 3. 跳转至管理看板
      router.push('/admin/dashboard')
    } catch (error) {
      const errorMsg = error.response?.data?.detail || '账号或密码错误'
      ElMessage.error(errorMsg)
      // 如果报错，确保清除可能存在的旧标记
      localStorage.removeItem('isAdmin')
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.admin-login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1a1c1e; /* 调深了一点，显得更专业 */
  position: relative;
  overflow: hidden;
}

/* 增加一个科技感的背景光晕 */
.bg-glow {
  position: absolute;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(64, 158, 255, 0.1) 0%, transparent 70%);
  z-index: 0;
}

.admin-login-card {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.3);
  z-index: 1;
}

.header { text-align: center; margin-bottom: 30px; }
.header h2 { margin-top: 15px; color: #303133; letter-spacing: 1px; }
.header p { font-size: 0.85rem; color: #909399; }
.login-btn { width: 100%; height: 45px; margin-top: 10px; font-weight: bold; }
.footer-links { text-align: center; margin-top: 20px; }
</style>