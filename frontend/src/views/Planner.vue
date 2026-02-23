<template>
  <div class="planner-container p-6">
    <el-row :gutter="24">
      <el-col :span="8">
        <el-card shadow="never" class="control-card mb-4">
          <template #header>
            <div class="flex items-center text-blue-600 font-bold">
              <el-icon class="mr-2"><MagicStick /></el-icon>AI 智能指令
            </div>
          </template>
          <el-input
            v-model="userRequirement"
            type="textarea"
            :rows="3"
            placeholder="输入指令，例如：'安排上午去故宫看古建，下午做漆扇'..."
          />
          <el-button type="primary" class="mt-4 w-full" :loading="aiLoading" @click="autoPlan">
            开始 AI 智能排产
          </el-button>
        </el-card>

        <el-card shadow="never" class="resource-card">
          <template #header>
            <div class="flex justify-between items-center">
              <span class="font-bold text-gray-700">原子积木仓</span>
              <el-tooltip content="刷新资源库" placement="top">
                <el-button link :icon="Refresh" @click="fetchActivities" />
              </el-tooltip>
            </div>
          </template>
          
          <el-input v-model="searchQuery" placeholder="搜索积木或基地..." prefix-icon="Search" class="mb-4" clearable />
          
          <div class="activity-pool">
            <el-collapse v-model="activeNames">
              <el-collapse-item 
                v-for="(group, location) in groupedActivities" 
                :key="location" 
                :name="location"
              >
                <template #title>
                  <div class="flex justify-between items-center w-full pr-4">
                    <span class="font-bold text-gray-600">
                      <el-icon class="mr-1"><Location /></el-icon>{{ location }} 
                      <small class="font-normal text-gray-400">({{ group.length }})</small>
                    </span>
                    <el-button 
                      size="small" 
                      type="primary" 
                      plain 
                      @click.stop="addAllFromLocation(group)"
                    >
                      全部加入
                    </el-button>
                  </div>
                </template>

                <div 
                  v-for="act in group" 
                  :key="act.id" 
                  class="block-item mini" 
                  @click="addToTimeline(act)"
                >
                  <div class="block-header">
                    <span class="title">{{ act.title }}</span>
                    <el-tag size="small" effect="plain">{{ act.duration }}min</el-tag>
                  </div>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card shadow="never">
          <template #header>
            <div class="flex justify-between items-center">
              <span class="font-bold text-green-600">行程路线预览 (可拖拽微调)</span>
              <div class="flex items-center gap-2">
                <el-button type="primary" plain @click="goToExportWorkbench">导出方案</el-button>
                <el-time-select
                  v-model="baseStartTime"
                  start="08:00" step="00:30" end="11:00"
                  @change="refreshSchedule"
                  style="width: 120px"
                />
              </div>
            </div>
          </template>

          <div class="timeline-container">
            <draggable v-model="timeline" item-key="temp_id" @change="refreshSchedule" handle=".drag-handle">
              <template #item="{ element, index }">
                <div class="timeline-item-wrapper">
                  <div class="time-indicator">
                    <div class="time-bubble">{{ element.display_time ? element.display_time.split(' - ')[0] : '--:--' }}</div>
                    <div class="line" v-if="index !== timeline.length - 1"></div>
                  </div>
                  <div class="itinerary-block">
                    <div class="drag-handle"><el-icon><Rank /></el-icon></div>
                    <div class="block-content">
                      <h4>{{ element.title }}</h4>
                      <p>📍 {{ element.location_name }} | ⏱️ {{ element.duration }} 分钟</p>
                    </div>
                    <el-button link type="danger" @click="removeNode(index)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                </div>
              </template>
            </draggable>
          </div>
          <el-empty v-if="timeline.length === 0" description="从左侧选择基地或积木开始排产" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import draggable from 'vuedraggable'
import axios from 'axios'
import { ElMessage, ElNotification } from 'element-plus'
import { useRouter } from 'vue-router'
import { MagicStick, Location, Rank, Delete, Search, Refresh } from '@element-plus/icons-vue'

const API_BASE = '/api/v1'
const router = useRouter()
const userRequirement = ref('')
const baseStartTime = ref('09:00')
const timeline = ref([])
const libraryActivities = ref([])
const searchQuery = ref('')
const aiLoading = ref(false)
const activeNames = ref([]) // 存储折叠面板展开状态
const TRANSITION_TIME = 15

// 加载资源库
const fetchActivities = async () => {
  try {
    const res = await axios.get(`${API_BASE}/activities`)
    libraryActivities.value = res.data
    // 默认展开第一个基地
    if (res.data.length > 0) {
      const firstLoc = res.data[0].location_name || '通用基地'
      activeNames.value = [firstLoc]
    }
  } catch (error) {
    ElMessage.error('积木库载入失败')
  }
}

onMounted(fetchActivities)

// 核心：按基地分组的计算属性
const groupedActivities = computed(() => {
  const filtered = libraryActivities.value.filter(a => 
    a.title.includes(searchQuery.value) || 
    (a.location_name && a.location_name.includes(searchQuery.value))
  )
  
  const groups = {}
  filtered.forEach(act => {
    const loc = act.location_name || '通用基地'
    if (!groups[loc]) groups[loc] = []
    groups[loc].push(act)
  })
  return groups
})

// 批量添加逻辑
const addAllFromLocation = (acts) => {
  const newItems = acts.map(act => ({
    ...act,
    temp_id: Date.now() + Math.random() + Math.random() // 确保 ID 唯一
  }))
  timeline.value.push(...newItems)
  refreshSchedule()
  ElMessage.success(`已将 ${acts.length} 个活动加入行程`)
}

const addToTimeline = (act) => {
  timeline.value.push({ ...act, temp_id: Date.now() + Math.random() })
  refreshSchedule()
}

const refreshSchedule = () => {
  if (timeline.value.length === 0) return
  let currentTime = new Date(`2026-01-01 ${baseStartTime.value}`)
  timeline.value = timeline.value.map((item) => {
    const startStr = currentTime.toTimeString().slice(0, 5)
    const endTime = new Date(currentTime.getTime() + item.duration * 60000)
    const endStr = endTime.toTimeString().slice(0, 5)
    currentTime = new Date(endTime.getTime() + TRANSITION_TIME * 60000)
    return { ...item, display_time: `${startStr} - ${endStr}` }
  })
}

const autoPlan = async () => {
  if (!userRequirement.value) return ElMessage.warning('请输入您的行程需求')
  aiLoading.value = true
  
  try {
    const res = await axios.post(`${API_BASE}/planner/ai-arrange`, {
      requirement: userRequirement.value
    })
    
    if (res.data.plan.length === 0) {
      return ElNotification({
        title: '未匹配到资源',
        message: 'AI 没能找到符合要求的基地，您可以尝试简化关键词。',
        type: 'info'
      })
    }

    // 1. 将所有匹配基地的积木一次性载入时间轴
    timeline.value = res.data.plan.map(act => ({
      ...act,
      temp_id: Date.now() + Math.random()
    }))
    
    // 2. 触发本地时间链计算
    refreshSchedule()
    
    // 3. 详细的成功反馈
    ElNotification({
      title: 'AI 联排成功',
      dangerouslyUseHTMLString: true,
      message: `已为您匹配基地：<b>${res.data.matched_bases.join('、')}</b><br/>共载入 ${res.data.plan.length} 个原子积木。`,
      type: 'success',
      duration: 6000
    })
  } catch (error) {
    ElMessage.error('AI 匹配失败，请检查后端 API')
  } finally {
    aiLoading.value = false
  }
}


const saveExportDraft = () => {
  const draft = {
    requirement: userRequirement.value,
    timeline: timeline.value.map(item => ({
      id: item.id,
      title: item.title,
      duration: item.duration,
      location_name: item.location_name,
      display_time: item.display_time
    }))
  }
  localStorage.setItem('planner_export_draft', JSON.stringify(draft))
}

const goToExportWorkbench = () => {
  if (timeline.value.length === 0) {
    ElMessage.warning('请先在排产工作台生成或添加活动后再导出')
    return
  }
  saveExportDraft()
  router.push('/export')
}

watch([timeline, userRequirement], () => {
  if (timeline.value.length > 0) {
    saveExportDraft()
  }
}, { deep: true })

const removeNode = (index) => {
  timeline.value.splice(index, 1)
  refreshSchedule()
}
</script>

<style scoped>
.planner-container { background-color: #f8fafc; min-height: 100vh; }

/* 资源库样式优化 */
.activity-pool :deep(.el-collapse) { border: none; }
.activity-pool :deep(.el-collapse-item__header) {
  height: auto; padding: 12px 0; line-height: 1.4; border-bottom: 1px solid #f1f5f9;
}
.activity-pool :deep(.el-collapse-item__content) { padding-bottom: 8px; padding-top: 8px; }

.block-item.mini {
  background: #fff; border: 1px solid #f1f5f9; border-radius: 6px;
  padding: 8px 12px; margin-bottom: 8px; cursor: pointer; transition: all 0.2s;
}
.block-item.mini:hover { border-color: #3b82f6; background-color: #eff6ff; }
.block-item.mini .title { font-size: 13px; color: #475569; }

/* 时间轴样式 */
.timeline-item-wrapper { display: flex; gap: 20px; }
.time-indicator { display: flex; flex-direction: column; align-items: center; width: 60px; }
.time-bubble { background: #3b82f6; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
.time-indicator .line { width: 2px; flex-grow: 1; background: #cbd5e1; margin: 4px 0; }
.itinerary-block {
  flex-grow: 1; background: white; border: 1px solid #e2e8f0; border-radius: 12px;
  padding: 16px; display: flex; align-items: center; margin-bottom: 20px;
}
.drag-handle { cursor: grab; color: #94a3b8; margin-right: 15px; }
</style>