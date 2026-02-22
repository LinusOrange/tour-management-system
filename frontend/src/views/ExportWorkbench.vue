<template>
  <div class="export-container p-6 bg-gray-50 min-h-screen">
    <el-page-header @back="$router.back()" title="文案生成与导出工作台" class="mb-6" />

    <el-row :gutter="24">
      <el-col :span="10">
        <el-card shadow="never" header="AI 文案引导配置">
          <el-alert title="您可以为每个部分输入自定义提示词，例如：'强调雷达信号处理的数学之美'" type="info" show-icon :closable="false" class="mb-4" />
          
          <el-form label-position="top">
            <el-form-item label="课程背景引导 (Section 2)">
              <el-input v-model="prompts.background" type="textarea" :rows="3" placeholder="默认：基于基地介绍自动生成" />
            </el-form-item>
            <el-form-item label="研学目标引导 (Section 3)">
              <el-input v-model="prompts.goals" type="textarea" :rows="3" placeholder="默认：根据积木教育目标整合" />
            </el-form-item>
            <el-form-item label="课程亮点引导 (Section 4)">
              <el-input v-model="prompts.highlights" type="textarea" :rows="3" placeholder="默认：智能提炼核心科技价值" />
            </el-form-item>
          </el-form>

          <el-button type="primary" size="large" class="w-full mt-4" :loading="generating" @click="startExport">
            {{ generating ? 'AI 正在深度创作中...' : '开始执行级联生成并导出 Word' }}
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
              <el-step title="准备基础资产数据" description="已从数据库加载基地画像与积木列表" />
              <el-step title="级联撰写：课程背景" :description="activeStep === 1 ? 'AI 正在检索基地底蕴...' : '生成完成'" />
              <el-step title="级联撰写：研学目标" :description="activeStep === 2 ? '正在进行维度对齐...' : '生成完成'" />
              <el-step title="级联撰写：课程亮点" :description="activeStep === 3 ? '正在提炼硬核科技价值...' : '生成完成'" />
              <el-step title="Word 文档渲染" description="正在进行格式编排与导出" />
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
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const prompts = ref({ background: '', goals: '', highlights: '' })
const generating = ref(false)
const exportDone = ref(false)
const activeStep = ref(0)
const progress = ref(0)

const startExport = async () => {
  generating.value = true
  activeStep.value = 1
  progress.value = 10
  
  // 模拟进度条增长（因为 API 响应时间较长）
  const timer = setInterval(() => {
    if (progress.value < 90) progress.value += 1
    if (progress.value === 30) activeStep.value = 2
    if (progress.value === 60) activeStep.value = 3
  }, 500)

  try {
    const res = await axios.post('/api/v1/export/word', {
      location_id: "当前选择的基地ID", // 需从 Planner 传过来
      activity_ids: ["积木ID_1", "积木ID_2"],
      custom_prompts: prompts.value
    }, { responseType: 'blob' })

    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `研学方案_${Date.now()}.docx`)
    document.body.appendChild(link)
    link.click()
    
    activeStep.value = 5
    progress.value = 100
    exportDone.value = true
    ElMessage.success('Word 方案生成成功！')
  } catch (e) {
    ElMessage.error('生成失败，请检查 AI 接口状态')
  } finally {
    clearInterval(timer)
    generating.value = false
  }
}
</script>