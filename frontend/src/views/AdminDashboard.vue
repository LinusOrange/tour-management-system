<template>
  <div class="admin-container">
    <h2>系统用户管理看板</h2>
    <el-table :data="userList" border style="width: 100%">
      <el-table-column prop="username" label="用户名" width="180" />
      <el-table-column prop="id" label="用户ID" />
      <el-table-column prop="activity_count" label="积木数量" width="120" />
      <el-table-column label="角色" width="120">
        <template #default="scope">
          <el-tag :type="scope.row.is_admin ? 'danger' : 'success'">
            {{ scope.row.is_admin ? '管理员' : '普通用户' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作">
        <template #default="scope">
          <el-button size="small" type="primary">重置密码</el-button>
          <el-button size="small" type="danger" @click="handleDelete(scope.row.id)">删除用户</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessageBox, ElMessage } from 'element-plus'

const userList = ref([])

const fetchUsers = async () => {
  try {
    const res = await axios.get('http://212.64.26.173:8000/api/v1/admin/users')
    userList.value = res.data
  } catch (err) {
    ElMessage.error("获取列表失败，请确认管理员权限")
  }
}

onMounted(fetchUsers)

const handleDelete = (userId) => {
  ElMessageBox.confirm('确定要删除该用户及其所有积木资产吗？此操作不可逆！', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    // 调用删除接口...
  })
}
</script>

<style scoped>
.admin-container { padding: 30px; background: #fff; border-radius: 8px; margin: 20px; }
</style>