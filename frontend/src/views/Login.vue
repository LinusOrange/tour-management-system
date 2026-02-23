<template>
  <div class="login-page">
    <div class="bg-decoration dec-1"></div>
    <div class="bg-decoration dec-2"></div>

    <div class="login-wrapper">
      <div class="login-side">
        <div class="side-content">
          <h1>研学原子积木</h1>
          <p>基于 AI 的研学方案策划工具。让您的方案设计像拼图一样精准、高效。</p>
          <div class="features">
            <span><el-icon><Monitor /></el-icon> 私人积木资产库</span>
            <span><el-icon><MagicStick /></el-icon> AI 智能排产逻辑</span>
            <span><el-icon><List /></el-icon> 一键生成导出方案</span>
          </div>
        </div>
      </div>

      <div class="login-main">
        <div class="login-content-inner">
          <div class="login-header">
            <h2>欢迎回来</h2>
            <p>请输入您的账号信息开始工作</p>
          </div>

          <el-form :model="loginForm" :rules="rules" ref="loginRef" label-position="top">
            <el-form-item label="用户名" prop="username">
              <el-input 
                v-model="loginForm.username" 
                placeholder="请输入用户名"
                :prefix-icon="User"
                size="large"
              />
            </el-form-item>
            
            <el-form-item label="密码" prop="password">
              <el-input 
                v-model="loginForm.password" 
                type="password" 
                placeholder="请输入密码"
                :prefix-icon="Lock"
                show-password
                size="large"
                @keyup.enter="handleLogin"
              />
            </el-form-item>

            <div class="form-footer">
              <el-checkbox v-model="rememberMe">记住我</el-checkbox>
              <el-button link type="primary">忘记密码？</el-button>
            </div>

            <el-button 
              type="primary" 
              class="login-btn" 
              :loading="loading" 
              @click="handleLogin"
            >
              登 录
            </el-button>

            <div class="admin-entry">
              <el-divider>系统管理</el-divider>
              <el-button link type="info" @click="$router.push('/admin/login')">管理员登录入口</el-button>
            </div>

            <div class="register-tip">
              还没有账号？ 
              <el-button link type="primary" @click="handleGoToRegister">立即注册</el-button>
            </div>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Monitor, MagicStick, List } from '@element-plus/icons-vue'

const router = useRouter()
const loginRef = ref(null)
const loading = ref(false)
const rememberMe = ref(true)

const loginForm = reactive({ username: '', password: '' })

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!loginRef.value) return
  await loginRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const res = await axios.post('/api/v1/auth/login', loginForm)
      localStorage.setItem('token', res.data.access_token)
      localStorage.setItem('username', loginForm.username)
      // 登录成功时，如果是管理员建议同步设置 isAdmin 标记
      // localStorage.setItem('isAdmin', res.data.is_admin ? 'true' : 'false')
      ElMessage.success('登录成功，欢迎回来！')
      router.push('/planner')
    } catch (error) {
      const errorMsg = error.response?.data?.detail || '登录失败，请检查账号密码'
      ElMessage.error(errorMsg)
    } finally {
      loading.value = false
    }
  })
}

const handleGoToRegister = () => {
  console.log("准备跳转至注册页...");
  router.push('/register').catch((err) => {
    console.error("路由跳转发生错误:", err);
    ElMessage.error("跳转失败，请确认路由配置");
  });
};
</script>

<style scoped>
.login-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); position: relative; overflow: hidden; }
.bg-decoration { position: absolute; border-radius: 50%; filter: blur(80px); z-index: 0; }
.dec-1 { width: 400px; height: 400px; background: rgba(64, 158, 255, 0.2); top: -100px; left: -100px; }
.dec-2 { width: 300px; height: 300px; background: rgba(103, 194, 58, 0.15); bottom: -50px; right: -50px; }

.login-wrapper { 
  display: flex; 
  width: 900px; 
  height: 600px; /* 增加高度以容纳管理员入口 */
  background: rgba(255, 255, 255, 0.8); 
  backdrop-filter: blur(15px); 
  border-radius: 20px; 
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.1); 
  overflow: hidden; 
  z-index: 1; 
}

.login-side { flex: 1; background: linear-gradient(135deg, #409EFF 0%, #3a8ee6 100%); display: flex; align-items: center; justify-content: center; padding: 40px; color: #fff; }
.side-content h1 { font-size: 2.5rem; margin-bottom: 20px; font-weight: 800; }
.side-content p { line-height: 1.6; opacity: 0.9; margin-bottom: 30px; }
.features { display: flex; flex-direction: column; gap: 12px; }
.features span { display: flex; align-items: center; gap: 8px; font-size: 0.9rem; }

.login-main { 
  flex: 1.2; 
  padding: 40px 50px; 
  background: #fff; 
  display: flex;
  flex-direction: column;
  justify-content: center; /* 垂直居中所有表单内容 */
}

.login-header { margin-bottom: 30px; }
.login-header h2 { font-size: 1.8rem; color: #303133; margin-bottom: 8px; }
.login-header p { color: #909399; font-size: 0.9rem; }

.form-footer { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }

.login-btn { width: 100%; height: 45px; font-size: 1.1rem; border-radius: 8px; margin-bottom: 10px; }

.admin-entry { margin: 20px 0; text-align: center; }
.admin-entry :deep(.el-divider__text) { background-color: #fff; color: #909399; font-size: 12px; }

.register-tip { text-align: center; font-size: 0.85rem; color: #606266; }
</style>