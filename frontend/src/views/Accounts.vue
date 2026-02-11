<template>
  <div class="accounts-page">
    <div class="page-header">
      <h2 class="page-title">账号管理</h2>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>
        新建账号
      </el-button>
    </div>

    <el-card shadow="hover">
      <el-table :data="accounts" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="account_name" label="账号名" width="140" />
        <el-table-column label="Cookie 状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.cookie_status === 'valid' ? 'success' : row.cookie_status === 'empty' ? 'info' : 'danger'" size="small">
              {{ row.cookie_status === 'valid' ? '已配置' : row.cookie_status === 'empty' ? '未配置' : '未知' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="定时签到" width="120">
          <template #default="{ row }">
            <el-switch v-model="row.schedule_enabled" size="small" @change="toggleSchedule(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="schedule_time" label="签到时间" width="100" />
        <el-table-column label="最近签到" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.last_checkin_status" size="small" :type="row.last_checkin_status === 'success' ? 'success' : 'danger'">
              {{ row.last_checkin_status }}
            </el-tag>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="sendkey" label="SendKey" width="100" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.sendkey ? '已配置' : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="success" @click="doCheckin(row)" :loading="row._checkinLoading">签到</el-button>
            <el-button size="small" type="warning" @click="doValidate(row)" :loading="row._validateLoading">验证</el-button>
            <el-popconfirm title="确定删除此账号？" @confirm="doDelete(row)">
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑账号' : '新建账号'"
      width="520px"
      destroy-on-close
    >
      <el-form :model="form" label-width="100px">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="基础信息" name="basic">
            <div style="max-height: 400px; overflow-y: auto; padding-right: 10px;">
              <el-form-item label="账号名" required>
                <el-input v-model="form.account_name" :disabled="isEdit" placeholder="唯一标识" />
              </el-form-item>
              <el-form-item label="Cookie SUB">
                <el-input v-model="form.cookie_sub" placeholder="留空则不更新" type="textarea" :rows="3" />
              </el-form-item>
              <el-form-item label="Cookie SUBP">
                <el-input v-model="form.cookie_subp" placeholder="留空则不更新" />
              </el-form-item>
              <el-form-item label="Cookie _T_WM">
                <el-input v-model="form.cookie_twm" placeholder="留空则不更新" />
              </el-form-item>
            </div>
          </el-tab-pane>

          <el-tab-pane label="定时设置" name="schedule">
            <el-form-item label="启用定时">
              <el-switch v-model="form.schedule_enabled" />
            </el-form-item>
            <el-form-item label="签到时间">
              <el-time-picker
                v-model="form._time"
                format="HH:mm"
                value-format="HH:mm"
                placeholder="选择时间"
              />
            </el-form-item>
            <el-form-item label="随机延迟(s)">
              <el-input-number v-model="form.schedule_random_delay" :min="0" :max="86400" />
            </el-form-item>
          </el-tab-pane>

          <el-tab-pane label="高级设置" name="advanced">
            <el-form-item label="重试次数">
              <el-input-number v-model="form.retry_count" :min="0" :max="10" />
            </el-form-item>
            <el-form-item label="请求间隔(s)">
              <el-input-number v-model="form.request_interval" :min="1" :max="30" :step="0.5" />
            </el-form-item>
            <el-form-item label="SendKey">
              <el-input v-model="form.sendkey" placeholder="Server酱推送密钥（可选）" />
            </el-form-item>
          </el-tab-pane>
        </el-tabs>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { accountApi, taskApi } from '@/api'

const loading = ref(false)
const accounts = ref<any[]>([])

const dialogVisible = ref(false)
const isEdit = ref(false)
const activeTab = ref('basic')
const editId = ref(0)
const submitLoading = ref(false)

const defaultForm = {
  account_name: '',
  cookie_sub: '',
  cookie_subp: '',
  cookie_twm: '',
  schedule_enabled: false,
  _time: '08:00',
  schedule_time: '08:00',
  schedule_random_delay: 300,
  retry_count: 2,
  request_interval: 3,
  sendkey: '',
}

const form = reactive({ ...defaultForm })

async function loadAccounts() {
  loading.value = true
  try {
    const res = await accountApi.list(0, 200)
    accounts.value = res.data.map((a: any) => ({ ...a, _checkinLoading: false, _validateLoading: false }))
  } finally {
    loading.value = false
  }
}

function openCreate() {
  Object.assign(form, { ...defaultForm })
  isEdit.value = false
  activeTab.value = 'basic'
  dialogVisible.value = true
}

function openEdit(row: any) {
  isEdit.value = true
  editId.value = row.id
  activeTab.value = 'basic'
  Object.assign(form, {
    account_name: row.account_name,
    cookie_sub: '',
    cookie_subp: '',
    cookie_twm: '',
    schedule_enabled: row.schedule_enabled,
    _time: row.schedule_time || '08:00',
    schedule_time: row.schedule_time || '08:00',
    schedule_random_delay: row.schedule_random_delay ?? 300,
    retry_count: row.retry_count ?? 2,
    request_interval: row.request_interval ?? 3,
    sendkey: row.sendkey || '',
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.account_name.trim()) {
    ElMessage.warning('账号名不能为空')
    return
  }

  submitLoading.value = true
  const data: any = {
    account_name: form.account_name.trim(),
    schedule_enabled: form.schedule_enabled,
    schedule_time: form._time || form.schedule_time,
    schedule_random_delay: form.schedule_random_delay,
    retry_count: form.retry_count,
    request_interval: form.request_interval,
    sendkey: form.sendkey || null,
  }

  // 只在有值时提交 cookie 字段
  if (form.cookie_sub) data.cookie_sub = form.cookie_sub
  if (form.cookie_subp) data.cookie_subp = form.cookie_subp
  if (form.cookie_twm) data.cookie_twm = form.cookie_twm

  try {
    if (isEdit.value) {
      await accountApi.update(editId.value, data)
      ElMessage.success('账号已更新')
    } else {
      await accountApi.create(data)
      ElMessage.success('账号已创建')
    }
    dialogVisible.value = false
    await loadAccounts()
  } finally {
    submitLoading.value = false
  }
}

async function toggleSchedule(row: any) {
  try {
    await accountApi.update(row.id, { schedule_enabled: row.schedule_enabled })
    await taskApi.applySchedule(row.id)
    ElMessage.success(row.schedule_enabled ? '定时已启用' : '定时已禁用')
  } catch {
    row.schedule_enabled = !row.schedule_enabled
  }
}

async function doCheckin(row: any) {
  row._checkinLoading = true
  try {
    const res = await taskApi.checkin(row.id)
    ElMessage.success(res.data.message || '签到完成')
    await loadAccounts()
  } finally {
    row._checkinLoading = false
  }
}

async function doValidate(row: any) {
  row._validateLoading = true
  try {
    const res = await taskApi.validateCookie(row.id)
    if (res.data.ok) {
      ElMessage.success('Cookie 有效')
    } else {
      ElMessage.error(res.data.message || 'Cookie 已失效')
    }
  } finally {
    row._validateLoading = false
  }
}

async function doDelete(row: any) {
  await accountApi.delete(row.id)
  ElMessage.success('账号已删除')
  await loadAccounts()
}

onMounted(loadAccounts)
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-title {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.text-muted {
  color: #c0c4cc;
}
</style>
