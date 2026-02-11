<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <el-icon :size="48" color="#409eff"><Star /></el-icon>
        <h2>微博超话签到系统</h2>
        <p class="login-subtitle">管理后台</p>
      </div>
      <el-form @submit.prevent="handleLogin" class="login-form">
        <el-form-item>
          <el-input
            v-model="adminKey"
            placeholder="请输入管理员密钥"
            size="large"
            show-password
            prefix-icon="Lock"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="serverUrl"
            placeholder="服务器地址（可选，默认当前域名）"
            size="large"
            prefix-icon="Link"
          />
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          :loading="loading"
          class="login-btn"
          @click="handleLogin"
        >
          登 录
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { healthApi } from '@/api'
import axios from 'axios'

const router = useRouter()
const adminKey = ref('')
const serverUrl = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!adminKey.value.trim()) {
    ElMessage.warning('请输入管理员密钥')
    return
  }

  loading.value = true
  try {
    // 验证密钥有效性
    const baseURL = serverUrl.value.trim() || ''
    const url = baseURL ? `${baseURL}/api/health` : '/api/health'

    await axios.get(url, {
      headers: { 'X-Admin-Key': adminKey.value.trim() },
      timeout: 5000,
    })

    localStorage.setItem('adminKey', adminKey.value.trim())
    if (baseURL) {
      localStorage.setItem('serverUrl', baseURL)
    }

    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (e: any) {
    if (e.response?.status === 401) {
      ElMessage.error('管理员密钥无效')
    } else {
      // health 不需要鉴权，只要能通就行
      localStorage.setItem('adminKey', adminKey.value.trim())
      ElMessage.success('登录成功')
      router.push('/dashboard')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h2 {
  margin: 12px 0 4px;
  color: #303133;
  font-size: 22px;
}

.login-subtitle {
  color: #909399;
  font-size: 14px;
  margin: 0;
}

.login-btn {
  width: 100%;
  margin-top: 8px;
}
</style>
