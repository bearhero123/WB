<template>
  <div class="keys-page">
    <div class="page-header">
      <h2 class="page-title">密钥管理</h2>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>
        生成密钥
      </el-button>
    </div>

    <el-card shadow="hover">
      <el-table :data="keys" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="label" label="标签" width="140" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'danger'" size="small">
              {{ row.enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="绑定账号" width="140">
          <template #default="{ row }">
            {{ row.bound_account_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="过期时间" width="180">
          <template #default="{ row }">
            {{ row.expires_at ? formatTime(row.expires_at) : '永不过期' }}
          </template>
        </el-table-column>
        <el-table-column label="最近使用" width="180">
          <template #default="{ row }">
            {{ row.last_used_at ? formatTime(row.last_used_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" :type="row.enabled ? 'warning' : 'success'" @click="toggleKey(row)">
              {{ row.enabled ? '禁用' : '启用' }}
            </el-button>
            <el-popconfirm title="确定删除此密钥？" @confirm="doDelete(row)">
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建对话框 -->
    <el-dialog
      v-model="createVisible"
      title="生成密钥"
      width="460px"
      destroy-on-close
    >
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="标签">
          <el-input v-model="createForm.label" placeholder="备注说明（可选）" />
        </el-form-item>
        <el-form-item label="绑定账号">
          <el-select v-model="createForm.bound_account_id" clearable placeholder="可选" style="width: 100%">
            <el-option
              v-for="acc in accountOptions"
              :key="acc.id"
              :label="acc.account_name"
              :value="acc.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="过期时间">
          <el-date-picker
            v-model="createForm.expires_at"
            type="datetime"
            placeholder="留空则永不过期"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="submitLoading">生成</el-button>
      </template>
    </el-dialog>

    <!-- 密钥展示 -->
    <el-dialog
      v-model="keyShowVisible"
      title="密钥已生成"
      width="520px"
    >
      <el-alert type="warning" :closable="false" style="margin-bottom: 16px">
        请立即复制密钥，关闭后将无法再次查看！
      </el-alert>
      <el-input v-model="generatedKey" readonly>
        <template #append>
          <el-button @click="copyKey">复制</el-button>
        </template>
      </el-input>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="editVisible"
      title="编辑密钥"
      width="460px"
      destroy-on-close
    >
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="标签">
          <el-input v-model="editForm.label" />
        </el-form-item>
        <el-form-item label="绑定账号">
          <el-select v-model="editForm.bound_account_id" clearable placeholder="可选" style="width: 100%">
            <el-option
              v-for="acc in accountOptions"
              :key="acc.id"
              :label="acc.account_name"
              :value="acc.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="过期时间">
          <el-date-picker
            v-model="editForm.expires_at"
            type="datetime"
            placeholder="留空则永不过期"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="handleEdit" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { keyApi, accountApi } from '@/api'
import dayjs from 'dayjs'

const loading = ref(false)
const keys = ref<any[]>([])
const accountOptions = ref<any[]>([])
const submitLoading = ref(false)

const createVisible = ref(false)
const createForm = reactive({ label: '', bound_account_id: null as number | null, expires_at: '' })

const keyShowVisible = ref(false)
const generatedKey = ref('')

const editVisible = ref(false)
const editId = ref(0)
const editForm = reactive({ label: '', bound_account_id: null as number | null, expires_at: '' })

function formatTime(t: string) {
  return t ? dayjs(t).format('YYYY-MM-DD HH:mm:ss') : '-'
}

async function loadKeys() {
  loading.value = true
  try {
    const res = await keyApi.list(0, 200)
    keys.value = res.data
  } finally {
    loading.value = false
  }
}

async function loadAccounts() {
  const res = await accountApi.list(0, 200)
  accountOptions.value = res.data
}

function openCreate() {
  createForm.label = ''
  createForm.bound_account_id = null
  createForm.expires_at = ''
  createVisible.value = true
}

async function handleCreate() {
  submitLoading.value = true
  try {
    const data: any = { label: createForm.label || null }
    if (createForm.bound_account_id) data.bound_account_id = createForm.bound_account_id
    if (createForm.expires_at) data.expires_at = new Date(createForm.expires_at).toISOString()

    const res = await keyApi.create(data)
    generatedKey.value = res.data.plain_key
    createVisible.value = false
    keyShowVisible.value = true
    ElMessage.success('密钥已生成')
    await loadKeys()
  } finally {
    submitLoading.value = false
  }
}

function copyKey() {
  navigator.clipboard.writeText(generatedKey.value)
  ElMessage.success('已复制到剪贴板')
}

function openEdit(row: any) {
  editId.value = row.id
  editForm.label = row.label || ''
  editForm.bound_account_id = row.bound_account_id || null
  editForm.expires_at = row.expires_at || ''
  editVisible.value = true
}

async function handleEdit() {
  submitLoading.value = true
  try {
    const data: any = { label: editForm.label || null }
    if (editForm.bound_account_id) {
      data.bound_account_id = editForm.bound_account_id
    } else {
      data.bound_account_id = null
    }
    if (editForm.expires_at) {
      data.expires_at = new Date(editForm.expires_at).toISOString()
    } else {
      data.expires_at = null
    }
    await keyApi.update(editId.value, data)
    ElMessage.success('密钥已更新')
    editVisible.value = false
    await loadKeys()
  } finally {
    submitLoading.value = false
  }
}

async function toggleKey(row: any) {
  await keyApi.update(row.id, { enabled: !row.enabled })
  ElMessage.success(row.enabled ? '密钥已禁用' : '密钥已启用')
  await loadKeys()
}

async function doDelete(row: any) {
  await keyApi.delete(row.id)
  ElMessage.success('密钥已删除')
  await loadKeys()
}

onMounted(() => {
  loadKeys()
  loadAccounts()
})
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
</style>
