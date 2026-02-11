<template>
  <div class="settings-page">
    <h2 class="page-title">系统设置</h2>

    <el-row :gutter="20">
      <!-- 系统信息 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>系统信息</span>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="服务状态">
              <el-tag :type="healthOk ? 'success' : 'danger'" size="small">
                {{ healthOk ? '运行中' : '异常' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="活跃定时任务">
              {{ schedulerJobs.length }}
            </el-descriptions-item>
            <el-descriptions-item label="服务器地址">
              {{ serverUrl || window.location.origin }}
            </el-descriptions-item>
          </el-descriptions>

          <div style="margin-top: 16px">
            <el-button type="primary" @click="checkHealth" :loading="healthLoading">
              <el-icon><Monitor /></el-icon>
              检测服务
            </el-button>
            <el-button type="success" @click="reloadSchedules" :loading="scheduleLoading">
              <el-icon><RefreshRight /></el-icon>
              重载定时
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 推送测试 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>推送测试</span>
          </template>
          <el-form label-width="80px">
            <el-form-item label="SendKey">
              <el-input v-model="testSendkey" placeholder="留空使用系统默认" />
            </el-form-item>
            <el-form-item>
              <el-button type="warning" @click="doTestPush" :loading="pushLoading">
                <el-icon><Bell /></el-icon>
                发送测试推送
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <!-- 调度器任务列表 -->
    <el-card shadow="hover" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>调度器任务列表</span>
          <el-button size="small" @click="loadScheduler" :loading="schedulerLoading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>
      <el-table :data="schedulerJobs" v-loading="schedulerLoading" stripe size="small">
        <el-table-column prop="id" label="Job ID" width="180" />
        <el-table-column prop="name" label="任务名" />
        <el-table-column prop="next_run_time" label="下次执行时间" width="220" />
      </el-table>
      <div v-if="schedulerJobs.length === 0 && !schedulerLoading" class="empty-text">
        暂无定时任务
      </div>
    </el-card>

    <!-- 管理员密钥更改 -->
    <el-card shadow="hover" style="margin-top: 20px">
      <template #header>
        <span>客户端设置</span>
      </template>
      <el-form label-width="120px" style="max-width: 500px">
        <el-form-item label="管理员密钥">
          <el-input v-model="adminKeyInput" show-password placeholder="当前登录密钥" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="updateAdminKey">更新本地密钥</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { healthApi, pushApi, taskApi } from '@/api'

const healthOk = ref(false)
const healthLoading = ref(false)
const scheduleLoading = ref(false)
const schedulerLoading = ref(false)
const pushLoading = ref(false)
const schedulerJobs = ref<any[]>([])
const testSendkey = ref('')
const adminKeyInput = ref('')
const serverUrl = ref(localStorage.getItem('serverUrl') || '')

const window = globalThis.window

async function checkHealth() {
  healthLoading.value = true
  try {
    const res = await healthApi.check()
    healthOk.value = res.data?.ok === true
    ElMessage.success('服务正常')
  } catch {
    healthOk.value = false
    ElMessage.error('服务异常')
  } finally {
    healthLoading.value = false
  }
}

async function loadScheduler() {
  schedulerLoading.value = true
  try {
    const res = await taskApi.schedulerStatus()
    schedulerJobs.value = res.data.jobs || []
  } finally {
    schedulerLoading.value = false
  }
}

async function reloadSchedules() {
  scheduleLoading.value = true
  try {
    const res = await taskApi.applySchedules()
    ElMessage.success(res.data.message || '定时已重载')
    await loadScheduler()
  } finally {
    scheduleLoading.value = false
  }
}

async function doTestPush() {
  pushLoading.value = true
  try {
    const res = await pushApi.test(testSendkey.value || undefined)
    if (res.data.ok) {
      ElMessage.success('测试推送已发送')
    } else {
      ElMessage.warning(res.data.message)
    }
  } finally {
    pushLoading.value = false
  }
}

function updateAdminKey() {
  if (!adminKeyInput.value.trim()) {
    ElMessage.warning('密钥不能为空')
    return
  }
  localStorage.setItem('adminKey', adminKeyInput.value.trim())
  ElMessage.success('本地密钥已更新')
}

onMounted(async () => {
  adminKeyInput.value = localStorage.getItem('adminKey') || ''
  await Promise.all([checkHealth(), loadScheduler()])
})
</script>

<style scoped>
.page-title {
  margin: 0 0 20px;
  font-size: 20px;
  color: #303133;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empty-text {
  text-align: center;
  color: #909399;
  padding: 20px 0;
}
</style>
