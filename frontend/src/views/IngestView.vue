<template>
  <el-container class="layout-container">
    <el-header>
      <div class="logo">研学原子积木 - AI 智能录入台</div>
    </el-header>
    
    <el-main>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card header="原始文案粘贴区">
            <el-input
              v-model="rawText"
              type="textarea"
              :rows="18"
              placeholder="请粘贴基地介绍、活动详情等文案..."
            />
            <div style="margin-top: 15px; text-align: right;">
              <el-button type="primary" :loading="loading" @click="startIngest">
                AI 智能分拣入库
              </el-button>
            </div>
          </el-card>
        </el-col>

        <el-col :span="12">
          <el-card header="分拣结果预览">
            <div v-if="result.location">
              <el-descriptions title="识别到的基地信息" :column="1" border>
                <el-descriptions-item label="基地名称">{{ result.location.name }}</el-descriptions-item>
                <el-descriptions-item label="基地地址">{{ result.location.address }}</el-descriptions-item>
                <el-descriptions-item label="标签">
                  <el-tag v-for="tag in result.location.tags" :key="tag" style="margin-right: 5px">{{ tag }}</el-tag>
                </el-descriptions-item>
              </el-descriptions>

              <h3 style="margin-top: 20px">原子积木列表 ({{ result.activities.length }})</h3>
              <el-timeline style="margin-top: 10px">
                <el-timeline-item
                  v-for="act in result.activities"
                  :key="act.id"
                  :timestamp="act.duration + ' 分钟'"
                  placement="top"
                >
                  <el-card>
                    <h4>{{ act.title }}</h4>
                    <p class="content-text">{{ act.content }}</p>
                    <div class="footer-info">
                      <el-tag size="small" type="info">
                        教育目标: {{ act.edu_goals ? Object.values(act.edu_goals).join('/') : '无' }}
                      </el-tag>
                    </div>
                  </el-card>
                </el-timeline-item>
              </el-timeline>
            </div>
            <el-empty v-else description="暂无数据，请在左侧点击分拣" />
          </el-card>
        </el-col>
      </el-row>
    </el-main>
  </el-container>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const rawText = ref('')
const loading = ref(false)
const result = ref({ location: null, activities: [] })

const startIngest = async () => {
  if (!rawText.value) return ElMessage.warning('请输入文本')
  
  // 1. 清空旧结果，显示加载状态
  result.value = { location: null, activities: [] }
  loading.value = true 
  
  try {
    const response = await axios.post('http://123.206.212.218:8000/api/v1/ai/mega-ingest', {
      raw_text: rawText.value
    })
    
    // 2. 这里的 response.data 现在包含了解析后的具体内容
    result.value = response.data 
    ElMessage.success('AI 解析成功，数据已同步入库！')
  } catch (error) {
    // ... 错误处理
  } finally {
    loading.value = false
  }
}

</script>

<style scoped>
.layout-container { height: 100vh; background: #f5f7fa; }
.logo { font-size: 20px; font-weight: bold; color: #409EFF; line-height: 60px; }
.content-text { font-size: 13px; color: #666; margin: 10px 0; line-height: 1.6; }
.footer-info { display: flex; justify-content: space-between; align-items: center; }
</style>