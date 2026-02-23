<template>
  <div class="login-page">
    <div class="bg-decoration dec-1"></div>
    <div class="bg-decoration dec-2"></div>

    <div class="login-wrapper">
      <div class="login-side register-bg">
        <div class="side-content">
          <h1>开启研学之旅</h1>
          <p>创建一个专属账号，开始构建您的私人原子积木库。利用 AI 驱动的工具，让行程策划变得从未如此高效。</p>
          <div class="steps">
            <div class="step-item">
              <el-icon><User /></el-icon>
              <span>创建唯一身份标识</span>
            </div>
            <div class="step-item">
              <el-icon><Lock /></el-icon>
              <span>设置高强度加密密码</span>
            </div>
            <div class="step-item">
              <el-icon><Files /></el-icon>
              <span>立即初始化资产库</span>
            </div>
          </div>
        </div>
      </div>

      <div class="login-main">
        <div class="login-card">
          <div class="login-header">
            <h2>注册新账号</h2>
            <p>加入研学原子积木系统，体验智能排产</p>
          </div>

          <el-form :model="regForm" :rules="rules" ref="regRef" label-position="top">
            <el-form-item label="用户名" prop="username">
              <el-input 
                v-model="regForm.username" 
                placeholder="建议 3 位以上中英文组合" 
                :prefix-icon="User" 
                size="large" 
              />
            </el-form-item>
            
            <el-form-item label="设置密码" prop="password">
              <el-input 
                v-model="regForm.password" 
                type="password" 
                placeholder="请输入至少 6 位密码" 
                :prefix-icon="Lock" 
                show-password 
                size="large" 
              />
            </el-form-item>

            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input 
                v-model="regForm.confirmPassword" 
                type="password" 
                placeholder="请再次输入以确认" 
                :prefix-icon="CircleCheck" 
                show-password 
                size="large" 
                @keyup.enter="handleRegister"
              />
            </el-form-item>

            <el-button 
              type="primary" 
              class="login-btn mt-4" 
              :loading="loading" 
              @click="handleRegister"
            >
              立即创建账号
            </el-button>

            <div class="register-tip">
              已有账号？ 
              <el-button link type="primary" @click="$router.push('/login')">返回登录</el-button>
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
import { User, Lock, CircleCheck, Files } from '@element-plus/icons-vue'

const router = useRouter()
const regRef = ref(null)
const loading = ref(false)

// 1. 表单数据模型
const regForm = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

// 2. 自定义校验：验证两次密码是否一致
const validatePass2 = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== regForm.password) {
    callback(new Error('两次输入密码不一致!'))
  } else {
    callback()
  }
}

// 3. 校验规则定义
const rules = {
  username: [
    { required: true, message: '用户名不能为空', trigger: 'blur' },
    { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请设置密码', trigger: 'blur' },
    { min: 6, max: 72, message: '密码长度需在 6 到 72 位之间', trigger: 'blur' } // 增加 max 限制
  ],
  confirmPassword: [
    { required: true, message: '请确认您的密码', trigger: 'blur' },
    { validator: validatePass2, trigger: 'blur' }
  ]
}

// 4. 执行注册逻辑
const handleRegister = async () => {
  if (!regRef.value) return
  
  // 提交前先执行表单验证
  await regRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      // 仅向后端发送 username 和 password
      await axios.post('/api/v1/auth/register', {
        username: regForm.username,
        password: regForm.password
      })
      
      ElMessage.success('注册成功！欢迎加入研学系统')
      // 注册成功后延迟跳转，让用户看清提示
      setTimeout(() => {
        router.push('/login')
      }, 1500)
    } catch (error) {
      // 捕获后端返回的错误信息（如用户名已占用）
      const msg = error.response?.data?.detail || '注册失败，请稍后重试'
      ElMessage.error(msg)
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
/* 核心布局逻辑 */
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  position: relative;
  overflow: hidden;
}

.bg-decoration {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  z-index: 0;
}
.dec-1 { width: 450px; height: 450px; background: rgba(103, 194, 58, 0.15); top: -100px; left: -100px; }
.dec-2 { width: 350px; height: 350px; background: rgba(64, 158, 255, 0.15); bottom: -50px; right: -50px; }

.login-wrapper {
  display: flex;
  width: 950px;
  height: 600px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(15px);
  border-radius: 24px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  z-index: 1;
}

/* 左侧注册引导区样式 */
.login-side {
  flex: 1;
  background: linear-gradient(135deg, #67C23A 0%, #529b2e 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #fff;
}
.side-content h1 { font-size: 2.8rem; margin-bottom: 24px; font-weight: 800; }
.side-content p { line-height: 1.8; opacity: 0.95; margin-bottom: 40px; font-size: 1.05rem; }

.steps { display: flex; flex-direction: column; gap: 20px; }
.step-item { display: flex; align-items: center; gap: 12px; font-size: 1rem; }

/* 右侧表单区样式 */
.login-main {
  flex: 1.1;
  padding: 60px;
  background: #fff;
}
.login-header { margin-bottom: 40px; }
.login-header h2 { font-size: 1.8rem; color: #303133; margin-bottom: 12px; }
.login-header p { color: #909399; font-size: 0.95rem; }

.login-btn {
  width: 100%;
  height: 48px;
  font-size: 1.1rem;
  border-radius: 10px;
  margin-bottom: 24px;
}

.register-tip {
  text-align: center;
  font-size: 0.9rem;
  color: #606266;
}
.mt-4 { margin-top: 16px; }
</style>