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
            placeholder="输入指令，例如：安排 3-4 天行程，上午科技馆，下午实践活动..."
          />
          <el-button type="primary" class="mt-4 w-full" :loading="aiLoading" @click="autoPlan">
            开始 AI 智能排产
          </el-button>
          <p class="constraint-tip mt-3">
            自动排产规则：上午不晚于 12:00，下午 14:00-18:00；超出当天自动顺延到下一天。
          </p>
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
              <el-collapse-item v-for="(group, location) in groupedActivities" :key="location" :name="location">
                <template #title>
                  <div class="flex justify-between items-center w-full pr-4">
                    <span class="font-bold text-gray-600">
                      <el-icon class="mr-1"><Location /></el-icon>{{ location }}
                      <small class="font-normal text-gray-400">({{ group.length }})</small>
                    </span>
                    <el-button size="small" type="primary" plain @click.stop="addAllFromLocation(group)">全部加入</el-button>
                  </div>
                </template>

                <div v-for="act in group" :key="act.id" class="block-item mini" @click="addToTimeline(act)">
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
              <span class="font-bold text-green-600">行程路线预览 (支持多日与手动微调)</span>
              <div class="flex items-center gap-2">
                <el-button type="primary" plain @click="goToExportWorkbench">导出方案</el-button>
                <el-time-select
                  v-model="baseStartTime"
                  start="08:00"
                  step="00:30"
                  end="11:00"
                  @change="refreshSchedule"
                  style="width: 130px"
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
                      <p>📍 {{ element.location_name }} | ⏱️ {{ element.manual_duration || element.duration }} 分钟</p>

                      <div class="editor-row">
                        <el-input-number
                          v-model="element.manual_day"
                          :min="1"
                          :max="30"
                          :step="1"
                          controls-position="right"
                          @change="refreshSchedule"
                        />
                        <el-time-select
                          v-model="element.manual_start_time"
                          placeholder="手动开始时间"
                          start="08:00"
                          step="00:05"
                          end="18:00"
                          clearable
                          style="width: 140px"
                          @change="refreshSchedule"
                        />
                        <el-input-number
                          v-model="element.manual_duration"
                          :min="10"
                          :max="480"
                          :step="5"
                          controls-position="right"
                          @change="refreshSchedule"
                        />
                        <span class="hint">天数/时间/时长手调，仅本次排产有效</span>
                      </div>
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
const activeNames = ref([])

const TRANSITION_TIME = 15
const MORNING_END = 12 * 60
const AFTERNOON_START = 14 * 60
const DAY_END = 18 * 60

const parseTimeToMinutes = (time) => {
  if (!time) return null
  const [h, m] = time.split(':').map(Number)
  return h * 60 + m
}

const formatMinutes = (minutes) => {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
}

const normalizeIntoWindow = (minute) => {
  if (minute >= MORNING_END && minute < AFTERNOON_START) return AFTERNOON_START
  return minute
}

const nextDayStart = () => parseTimeToMinutes(baseStartTime.value) || 9 * 60

const ensureSchedulableItem = (item) => ({
  ...item,
  manual_day: Number(item.manual_day) || 0,
  manual_duration: Number(item.manual_duration) || Number(item.duration),
  manual_start_time: item.manual_start_time || ''
})

const fetchActivities = async () => {
  try {
    const res = await axios.get(`${API_BASE}/activities`)
    libraryActivities.value = res.data
    if (res.data.length > 0) {
      const firstLoc = res.data[0].location_name || '通用基地'
      activeNames.value = [firstLoc]
    }
  } catch (error) {
    ElMessage.error('积木库载入失败')
  }
}

onMounted(fetchActivities)

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

const addAllFromLocation = (acts) => {
  const newItems = acts.map(act => ensureSchedulableItem({ ...act, temp_id: Date.now() + Math.random() + Math.random() }))
  timeline.value.push(...newItems)
  refreshSchedule()
  ElMessage.success(`已将 ${acts.length} 个活动加入行程`)
}

const addToTimeline = (act) => {
  timeline.value.push(ensureSchedulableItem({ ...act, temp_id: Date.now() + Math.random() }))
  refreshSchedule()
}

const refreshSchedule = () => {
  if (timeline.value.length === 0) return

  let day = 1
  let current = nextDayStart()

  timeline.value = timeline.value.map((rawItem) => {
    const item = ensureSchedulableItem(rawItem)
    const duration = item.manual_duration > 0 ? item.manual_duration : Number(item.duration)

    // 手动指定天数（仅本次排产）
    if (item.manual_day && item.manual_day > day) {
      day = item.manual_day
      current = nextDayStart()
    }

    let start = item.manual_start_time ? parseTimeToMinutes(item.manual_start_time) : current
    start = normalizeIntoWindow(start)

    // 上午放不下则进入下午
    if (start < MORNING_END && start + duration > MORNING_END) {
      start = AFTERNOON_START
    }

    // 当天下午放不下则滚动到下一天
    while (start + duration > DAY_END) {
      day += 1
      start = nextDayStart()
      start = normalizeIntoWindow(start)
      if (start < MORNING_END && start + duration > MORNING_END) {
        start = AFTERNOON_START
      }
    }

    const end = start + duration

    current = normalizeIntoWindow(end + TRANSITION_TIME)
    if (current >= DAY_END) {
      day += 1
      current = nextDayStart()
    }

    return {
      ...item,
      manual_day: item.manual_day || day,
      manual_duration: duration,
      display_time: `D${day} ${formatMinutes(start)} - ${formatMinutes(end)}`
    }
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

    timeline.value = res.data.plan.map(act => ensureSchedulableItem({
      ...act,
      temp_id: Date.now() + Math.random()
    }))

    refreshSchedule()

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
      duration: item.manual_duration || item.duration,
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
.activity-pool :deep(.el-collapse) { border: none; }
.activity-pool :deep(.el-collapse-item__header) {
  height: auto;
  padding: 12px 0;
  line-height: 1.4;
  border-bottom: 1px solid #f1f5f9;
}
.activity-pool :deep(.el-collapse-item__content) { padding-bottom: 8px; padding-top: 8px; }

.block-item.mini {
  background: #fff;
  border: 1px solid #f1f5f9;
  border-radius: 6px;
  padding: 8px 12px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.block-item.mini:hover { border-color: #3b82f6; background-color: #eff6ff; }
.block-item.mini .title { font-size: 13px; color: #475569; }

.timeline-item-wrapper { display: flex; gap: 20px; }
.time-indicator { display: flex; flex-direction: column; align-items: center; width: 95px; }
.time-bubble {
  background: #3b82f6;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
}
.time-indicator .line { width: 2px; flex-grow: 1; background: #cbd5e1; margin: 4px 0; }
.itinerary-block {
  flex-grow: 1;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}
.drag-handle { cursor: grab; color: #94a3b8; margin-right: 15px; }
.editor-row { display: flex; align-items: center; gap: 10px; margin-top: 10px; }
.hint { font-size: 12px; color: #64748b; }
.constraint-tip { font-size: 12px; color: #64748b; line-height: 1.4; }
</style>
