<template>
  <div class="dashboard">
    <h2 class="page-title">仪表盘</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #409eff">
            <el-icon :size="28"><User /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalAccounts }}</div>
            <div class="stat-label">账号总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #67c23a">
            <el-icon :size="28"><Clock /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.scheduledAccounts }}</div>
            <div class="stat-label">定时签到</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #e6a23c">
            <el-icon :size="28"><Key /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalKeys }}</div>
            <div class="stat-label">密钥总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #f56c6c">
            <el-icon :size="28"><Warning /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.schedulerJobs }}</div>
            <div class="stat-label">活跃任务</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>快捷操作</span>
          </template>
          <div class="quick-actions">
            <el-button type="primary" @click="checkinAll" :loading="checkinLoading">
              <el-icon><VideoPlay /></el-icon>
              全部签到
            </el-button>
            <el-button type="success" @click="applySchedules" :loading="scheduleLoading">
              <el-icon><RefreshRight /></el-icon>
              重载定时
            </el-button>
            <el-button type="warning" @click="testPush" :loading="pushLoading">
              <el-icon><Bell /></el-icon>
              测试推送
            </el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>调度器状态</span>
          </template>
          <div v-if="schedulerJobs.length === 0" class="empty-text">暂无定时任务</div>
          <el-table v-else :data="schedulerJobs" size="small" max-height="200">
            <el-table-column prop="name" label="任务" />
            <el-table-column prop="next_run_time" label="下次执行" width="180" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近日志 -->
    <el-card shadow="hover" style="margin-top: 20px">
      <template #header>
        <span>最近签到日志</span>
      </template>
      <el-table :data="recentLogs" size="small" stripe>
        <el-table-column prop="account_name" label="账号" width="140" />
        <el-table-column prop="event_type" label="事件" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="eventTypeMap[row.event_type] || 'info'">
              {{ row.event_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 'success' ? 'success' : 'danger'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="消息" show-overflow-tooltip />
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { accountApi, keyApi, taskApi, pushApi } from '@/api'
import dayjs from 'dayjs'

const stats = reactive({
  totalAccounts: 0,
  scheduledAccounts: 0,
  totalKeys: 0,
  schedulerJobs: 0,
})

const schedulerJobs = ref<any[]>([])
const recentLogs = ref<any[]>([])
const checkinLoading = ref(false)
const scheduleLoading = ref(false)
const pushLoading = ref(false)

const eventTypeMap: Record<string, string> = {
  checkin: '',
  cookie_update: 'success',
  cookie_invalid: 'danger',
  manual_checkin: 'warning',
}

function formatTime(t: string) {
  return t ? dayjs(t).format('YYYY-MM-DD HH:mm:ss') : '-'
}

async function loadData() {
  try {
    const [accRes, keyRes, schedRes, logRes] = await Promise.all([
      accountApi.list(0, 200),
      keyApi.list(0, 200),
      taskApi.schedulerStatus(),
      taskApi.logs({ limit: 10 }),
    ])

    const accounts = accRes.data
    stats.totalAccounts = accounts.length
    stats.scheduledAccounts = accounts.filter((a: any) => a.schedule_enabled).length

    stats.totalKeys = keyRes.data.length

    schedulerJobs.value = schedRes.data.jobs || []
    stats.schedulerJobs = schedulerJobs.value.length

    recentLogs.value = logRes.data
  } catch (e) {
    console.error('加载仪表盘数据失败', e)
  }
}

async function checkinAll() {
  checkinLoading.value = true
  try {
    const res = await taskApi.checkinAll()
    ElMessage.success(res.data.message || '签到完成')
    await loadData()
  } finally {
    checkinLoading.value = false
  }
}

async function applySchedules() {
  scheduleLoading.value = true
  try {
    const res = await taskApi.applySchedules()
    ElMessage.success(res.data.message || '定时已重载')
    await loadData()
  } finally {
    scheduleLoading.value = false
  }
}

async function testPush() {
  pushLoading.value = true
  try {
    const res = await pushApi.test()
    if (res.data.ok) {
      ElMessage.success('测试推送已发送')
    } else {
      ElMessage.warning(res.data.message)
    }
  } finally {
    pushLoading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.page-title {
  margin: 0 0 20px;
  font-size: 20px;
  color: #303133;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 0;
}

.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.quick-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.empty-text {
  text-align: center;
  color: #909399;
  padding: 20px 0;
}
</style>
