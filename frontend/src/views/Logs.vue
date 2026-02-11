<template>
  <div class="logs-page">
    <div class="page-header">
      <h2 class="page-title">任务日志</h2>
      <div class="filters">
        <el-select v-model="filters.event_type" clearable placeholder="事件类型" style="width: 140px" @change="loadLogs">
          <el-option label="签到" value="checkin" />
          <el-option label="Cookie更新" value="cookie_update" />
          <el-option label="Cookie失效" value="cookie_invalid" />
          <el-option label="手动签到" value="manual_checkin" />
        </el-select>
        <el-select v-model="filters.status" clearable placeholder="状态" style="width: 120px" @change="loadLogs">
          <el-option label="成功" value="success" />
          <el-option label="失败" value="fail" />
          <el-option label="部分" value="partial" />
        </el-select>
        <el-select v-model="filters.account_id" clearable placeholder="账号筛选" style="width: 160px" @change="loadLogs">
          <el-option
            v-for="acc in accountOptions"
            :key="acc.id"
            :label="acc.account_name"
            :value="acc.id"
          />
        </el-select>
        <el-button @click="loadLogs" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <el-card shadow="hover">
      <el-table :data="logs" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="account_name" label="账号" width="140">
          <template #default="{ row }">
            {{ row.account_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="event_type" label="事件类型" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="eventTagType(row.event_type)">
              {{ eventLabel(row.event_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="statusTagType(row.status)">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="消息" show-overflow-tooltip />
        <el-table-column label="详情" width="80">
          <template #default="{ row }">
            <el-button v-if="row.detail" size="small" link type="primary" @click="showDetail(row)">
              查看
            </el-button>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-button :disabled="filters.skip === 0" @click="prevPage">上一页</el-button>
        <span class="page-info">第 {{ currentPage }} 页</span>
        <el-button :disabled="logs.length < filters.limit" @click="nextPage">下一页</el-button>
      </div>
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="日志详情" width="600px">
      <pre class="detail-json">{{ detailContent }}</pre>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { taskApi, accountApi } from '@/api'
import { formatServerTime } from '@/utils/time'

const loading = ref(false)
const logs = ref<any[]>([])
const accountOptions = ref<any[]>([])
const detailVisible = ref(false)
const detailContent = ref('')

const filters = reactive({
  event_type: '',
  status: '',
  account_id: null as number | null,
  skip: 0,
  limit: 30,
})

const currentPage = computed(() => Math.floor(filters.skip / filters.limit) + 1)

function formatTime(t: string) {
  return formatServerTime(t)
}

function eventTagType(type: string): string {
  const map: Record<string, string> = {
    checkin: '',
    cookie_update: 'success',
    cookie_invalid: 'danger',
    manual_checkin: 'warning',
  }
  return map[type] || 'info'
}

function eventLabel(type: string): string {
  const map: Record<string, string> = {
    checkin: '定时签到',
    cookie_update: 'Cookie更新',
    cookie_invalid: 'Cookie失效',
    manual_checkin: '手动签到',
  }
  return map[type] || type
}

function statusTagType(status: string): string {
  if (status === 'success') return 'success'
  if (status === 'fail') return 'danger'
  if (status === 'partial') return 'warning'
  return 'info'
}

function showDetail(row: any) {
  detailContent.value = JSON.stringify(row.detail, null, 2)
  detailVisible.value = true
}

async function loadLogs() {
  loading.value = true
  try {
    const params: any = { skip: filters.skip, limit: filters.limit }
    if (filters.event_type) params.event_type = filters.event_type
    if (filters.status) params.status = filters.status
    if (filters.account_id) params.account_id = filters.account_id

    const res = await taskApi.logs(params)
    logs.value = res.data
  } finally {
    loading.value = false
  }
}

function prevPage() {
  filters.skip = Math.max(0, filters.skip - filters.limit)
  loadLogs()
}

function nextPage() {
  filters.skip += filters.limit
  loadLogs()
}

onMounted(async () => {
  const accRes = await accountApi.list(0, 200)
  accountOptions.value = accRes.data
  loadLogs()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.page-title {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 16px;
}

.page-info {
  color: #606266;
  font-size: 14px;
}

.detail-json {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  font-size: 13px;
  max-height: 400px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.text-muted {
  color: #c0c4cc;
}
</style>
