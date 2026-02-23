<template>
  <div class="export-container p-6 bg-gray-50 min-h-screen">
    <el-page-header @back="$router.back()" title="文案生成与导出工作台" class="mb-6" />

    <el-alert
      v-if="!hasDraft"
      title="未发现排产数据，请先在排产工作台完成行程编排后再导出。"
      type="warning"
      :closable="false"
      show-icon
      class="mb-4"
    />

    <el-row :gutter="24">
      <el-col :span="10">
        <el-card shadow="never" header="AI 文案引导配置">
          <el-alert title="每个章节会单独调用火山模型生成，支持自定义提示词微调风格。" type="info" show-icon :closable="false" class="mb-4" />

          <el-descriptions v-if="hasDraft" :column="1" border size="small" class="mb-4">
            <el-descriptions-item label="行程活动数">{{ draft.timeline.length }} 个</el-descriptions-item>
            <el-descriptions-item label="涉及基地">{{ locationSummary }}</el-descriptions-item>
            <el-descriptions-item label="用户需求">{{ draft.requirement || '未填写' }}</el-descriptions-item>
          </el-descriptions>

          <el-form label-position="top">
            <el-form-item label="第一部分：研学基地（Section 1）">
              <el-input v-model="prompts.section_1_base" type="textarea" :rows="2" placeholder="例如：强调基地在区域科技教育中的标杆作用" />
            </el-form-item>
            <el-form-item label="第二部分：课程背景（Section 2）">
              <el-input v-model="prompts.section_2_background" type="textarea" :rows="2" placeholder="例如：突出新课标与跨学科融合背景" />
            </el-form-item>
            <el-form-item label="第三部分：研学目标（Section 3）">
              <el-input v-model="prompts.section_3_goals" type="textarea" :rows="2" placeholder="例如：增加可量化评价指标" />
            </el-form-item>
            <el-form-item label="第四部分：课程亮点（Section 4）">
              <el-input v-model="prompts.section_4_highlights" type="textarea" :rows="2" placeholder="例如：强调项目式学习与成果展示" />
            </el-form-item>
            <el-form-item label="第五部分：研学流程（Section 5）">
              <el-input v-model="prompts.section_5_process" type="textarea" :rows="2" placeholder="例如：突出每个环节的衔接和反思任务" />
            </el-form-item>
          </el-form>

          <el-button type="primary" size="large" class="w-full mt-4" :loading="generating" :disabled="!hasDraft" @click="startExport">
            {{ generating ? '正在级联生成 Word 文案...' : '生成并导出 Word 方案' }}
          </el-button>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card shadow="never" header="生成流水线状态">
          <div class="pipeline-status py-10 text-center" v-if="!generating && !exportDone">
            <el-empty description="等待启动生成指令" />
          </div>

          <div v-else class="py-4">
            <el-steps :active="activeStep" finish-status="success" direction="vertical">
              <el-step title="准备排产数据" description="读取排产工作台时间轴与需求" />
              <el-step title="生成第一部分：研学基地" />
              <el-step title="生成第二~四部分：背景/目标/亮点" />
              <el-step title="生成第五部分：研学流程" />
              <el-step title="Word 文档渲染与下载" />
            </el-steps>

            <el-progress
              v-if="generating"
              :percentage="progress"
              :stroke-width="20"
              striped
              striped-flow
              class="mt-10"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const prompts = ref({
  section_1_base: '',
  section_2_background: '',
  section_3_goals: '',
  section_4_highlights: '',
  section_5_process: ''
})

const draft = ref({ requirement: '', timeline: [] })
const generating = ref(false)
const exportDone = ref(false)
const activeStep = ref(0)
const progress = ref(0)

const hasDraft = computed(() => draft.value.timeline && draft.value.timeline.length > 0)
const locationSummary = computed(() => {
  const names = [...new Set(draft.value.timeline.map(item => item.location_name).filter(Boolean))]
  return names.length ? names.join('、') : '待补充'
})

onMounted(() => {
  const cache = localStorage.getItem('planner_export_draft')
  if (!cache) return
  try {
    draft.value = JSON.parse(cache)
  } catch {
    ElMessage.warning('排产缓存解析失败，请返回排产工作台重新生成。')
  }
})

const startExport = async () => {
  if (!hasDraft.value) {
    ElMessage.warning('请先在排产工作台准备好时间轴数据')
    return
  }

  generating.value = true
  exportDone.value = false
  activeStep.value = 1
  progress.value = 8

  const timer = setInterval(() => {
    if (progress.value < 90) progress.value += 2
    if (progress.value >= 20) activeStep.value = 2
    if (progress.value >= 45) activeStep.value = 3
    if (progress.value >= 70) activeStep.value = 4
  }, 500)

  try {
    const res = await axios.post('/api/v1/export/word', {
      requirement: draft.value.requirement || '',
      timeline: draft.value.timeline,
      custom_prompts: prompts.value
    }, { responseType: 'blob' })

    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `研学方案_${Date.now()}.docx`)
    document.body.appendChild(link)
    link.click()
    link.remove()

    activeStep.value = 5
    progress.value = 100
    exportDone.value = true
    ElMessage.success('Word 方案生成成功！')
  } catch (e) {
    const errorMsg = e.response?.data?.detail || '生成失败，请检查 AI 接口状态'
    ElMessage.error(errorMsg)
  } finally {
    clearInterval(timer)
    generating.value = false
  }
}
</script>
