<template>
  <div class="library-container p-6 bg-gray-50 min-h-screen">
    <el-row :gutter="20" class="mb-6">
      <el-col :span="6">
        <el-card shadow="hover" class="stats-card">
          <div class="flex items-center">
            <el-icon class="stats-icon bg-blue-100 text-blue-600"><Collection /></el-icon>
            <div class="ml-4">
              <div class="text-gray-400 text-xs">原子积木总数</div>
              <div class="text-2xl font-bold">{{ activities.length }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stats-card">
          <div class="flex items-center">
            <el-icon class="stats-icon bg-green-100 text-green-600"><OfficeBuilding /></el-icon>
            <div class="ml-4">
              <div class="text-gray-400 text-xs">覆盖研学基地</div>
              <div class="text-2xl font-bold">{{ uniqueLocationsCount }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stats-card">
          <div class="flex items-center">
            <el-icon class="stats-icon bg-purple-100 text-purple-600"><Compass /></el-icon>
            <div class="ml-4">
              <div class="text-gray-400 text-xs">AI 补全画像</div>
              <div class="text-2xl font-bold">{{ aiEnrichedCount }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stats-card">
          <div class="flex items-center">
            <el-icon class="stats-icon bg-orange-100 text-orange-600"><Timer /></el-icon>
            <div class="ml-4">
              <div class="text-gray-400 text-xs">库容总时长</div>
              <div class="text-2xl font-bold">{{ totalDuration }} <span class="text-xs">min</span></div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <template #header>
        <div class="flex justify-between items-center">
          <div class="flex items-center gap-4">
            <span class="font-bold text-lg text-gray-700">积木资产管理</span>
            <el-button 
              v-if="selectedIds.length > 0" 
              type="danger" 
              plain 
              @click="handleBulkDelete"
            >
              批量删除 ({{ selectedIds.length }})
            </el-button>
          </div>
          
          <div class="flex gap-2">
            <el-input 
              v-model="searchQuery" 
              placeholder="搜索积木或基地..." 
              prefix-icon="Search" 
              style="width: 250px" 
              clearable 
            />
            <el-button type="warning" plain @click="handleDeduplicate">一键去重</el-button>
            <el-button type="primary" @click="openAdd">新增原子积木</el-button>
          </div>
        </div>
      </template>

      <el-table 
        :data="filteredActivities" 
        v-loading="loading" 
        style="width: 100%"
        row-key="id"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="expand">
          <template #default="props">
            <div class="expand-wrapper p-6 m-2 rounded-lg">
              <div class="flex gap-6">
                <div class="location-avatar">
                  <el-icon :size="30"><Memo /></el-icon>
                </div>
                <div class="flex-1">
                  <div class="flex items-center gap-3 mb-2">
                    <span class="text-lg font-bold text-gray-800">{{ props.row.location_name }}</span>
                    <el-tag v-for="tag in props.row.location_tags" :key="tag" size="small" effect="plain">
                      {{ tag }}
                    </el-tag>
                  </div>
                  <div class="text-sm text-gray-500 mb-3 flex items-center">
                    <el-icon class="mr-1"><Location /></el-icon>
                    {{ props.row.location_address || '暂无详细地址' }}
                  </div>
                  <div class="description-box">
                    {{ props.row.location_description || '暂无详细基地画像，建议通过 AI 联网补全。' }}
                  </div>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="title" label="积木名称" min-width="180">
          <template #default="scope">
            <span class="font-bold text-gray-700">{{ scope.row.title }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="location_name" label="所属基地" width="200">
          <template #default="scope">
            <el-popover placement="top" :width="280" trigger="hover">
              <template #reference>
                <el-tag size="small" type="primary" effect="light" class="cursor-pointer">
                  {{ scope.row.location_name }}
                </el-tag>
              </template>
              <div class="text-xs">
                <p class="font-bold mb-1">地址预览：</p>
                <p class="text-gray-500 mb-2">{{ scope.row.location_address }}</p>
                <p class="font-bold mb-1">简介：</p>
                <p class="text-gray-500 line-clamp-3">{{ scope.row.location_description }}</p>
              </div>
            </el-popover>
          </template>
        </el-table-column>

        <el-table-column prop="duration" label="时长" width="120">
          <template #default="scope">
            <el-icon class="mr-1"><Timer /></el-icon>{{ scope.row.duration }} min
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button link type="primary" @click="openEdit(scope.row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(scope.row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '精修原子积木' : '新增原子积木'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="form.title" placeholder="如：雷达信号处理基础讲座" />
        </el-form-item>
        <el-form-item label="时长">
          <el-input-number v-model="form.duration" :min="1" :step="15" />
        </el-form-item>
        <el-form-item label="基地">
          <el-input v-model="form.location_name" placeholder="输入基地名，系统将自动联网补全画像" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="form.content" type="textarea" :rows="4" placeholder="积木核心流程描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">保存并同步</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Timer, Search, Collection, OfficeBuilding, 
  Compass, Memo, Location 
} from '@element-plus/icons-vue'

// --- 基础配置 ---
const API_BASE = 'http://123.206.212.218:8000/api/v1'
const loading = ref(false)
const activities = ref([])
const searchQuery = ref('')
const selectedIds = ref([])

// --- 统计逻辑 ---
const uniqueLocationsCount = computed(() => {
  return new Set(activities.value.map(a => a.location_name)).size
})

const aiEnrichedCount = computed(() => {
  return activities.value.filter(a => a.location_address && a.location_address !== '待补充').length
})

const totalDuration = computed(() => {
  return activities.value.reduce((sum, a) => sum + (a.duration || 0), 0)
})

// --- 数据加载 ---
const fetchActivities = async () => {
  loading.value = true
  try {
    // 注意：此处需要后端 get_user_activities 返回 location 的详细字段
    const res = await axios.get(`${API_BASE}/activities`)
    activities.value = res.data
  } catch (error) {
    ElMessage.error('无法连接后端服务，请确认登录状态')
  } finally {
    loading.value = false
  }
}

onMounted(fetchActivities)

// --- 搜索过滤 ---
const filteredActivities = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return activities.value.filter(a => 
    a.title.toLowerCase().includes(q) || 
    a.location_name?.toLowerCase().includes(q)
  )
})

// --- CRUD 逻辑 ---
const dialogVisible = ref(false)
const isEdit = ref(false)
const form = ref({ id: '', title: '', duration: 60, location_name: '', content: '' })

const openAdd = () => {
  isEdit.value = false
  form.value = { id: '', title: '', duration: 60, location_name: '', content: '' }
  dialogVisible.value = true
}

const openEdit = (row) => {
  isEdit.value = true
  form.value = { ...row }
  dialogVisible.value = true
}

const submitForm = async () => {
  if (!form.value.title) return ElMessage.warning('名称不能为空')
  try {
    if (isEdit.value) {
      await axios.put(`${API_BASE}/activities/${form.value.id}`, form.value)
      ElMessage.success('修改成功')
    } else {
      await axios.post(`${API_BASE}/activities`, form.value)
      ElMessage.success('积木入库成功，AI 已启动基地画像补全')
    }
    dialogVisible.value = false
    fetchActivities()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const handleDelete = (id) => {
  ElMessageBox.confirm('确定删除吗？', '提示', { type: 'warning' }).then(async () => {
    await axios.delete(`${API_BASE}/activities/${id}`)
    ElMessage.success('已删除')
    fetchActivities()
  })
}

const handleSelectionChange = (val) => {
  selectedIds.value = val.map(i => i.id)
}

const handleBulkDelete = () => {
  ElMessageBox.confirm(`批量删除 ${selectedIds.value.length} 个积木？`, '警告', { type: 'error' }).then(async () => {
    await Promise.all(selectedIds.value.map(id => axios.delete(`${API_BASE}/activities/${id}`)))
    ElMessage.success('批量清理完成')
    fetchActivities()
  })
}

const handleDeduplicate = () => {
  const seen = new Set()
  const dupes = activities.value.filter(a => seen.has(a.title) ? true : !seen.add(a.title))
  if (dupes.length === 0) return ElMessage.success('库内无重复积木')
  
  ElMessageBox.confirm(`检测到 ${dupes.length} 个重复积木，是否一键清理？`).then(async () => {
    await Promise.all(dupes.map(d => axios.delete(`${API_BASE}/activities/${d.id}`)))
    fetchActivities()
  })
}
</script>

<style scoped>
.stats-card {
  border: none;
  border-radius: 12px;
  transition: all 0.3s cubic-bezier(.25,.8,.25,1);
}
.stats-card:hover { transform: translateY(-4px); }
.stats-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}
.expand-wrapper {
  background: linear-gradient(135deg, #f8faff 0%, #ffffff 100%);
  border-left: 4px solid #409eff;
}
.location-avatar {
  background: white;
  padding: 15px;
  border-radius: 50%;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  color: #409eff;
}
.description-box {
  background: rgba(255,255,255,0.7);
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #eef2f8;
  color: #606266;
  font-style: italic;
  font-size: 13px;
  line-height: 1.6;
}
</style>