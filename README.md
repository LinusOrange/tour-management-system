# 研学原子积木系统（Tour Management System）

一个面向研学场景的全栈系统：
- 录入基地与活动原子积木（支持 AI 分拣）
- 根据需求进行智能排产
- 生成五段式课程方案文案并导出 Word
- 支持多用户隔离与管理员视图

---

## 1. 功能概览

### 1.1 核心业务模块
- **AI 资源录入台**（`/ingest`）
  - 粘贴原始文案
  - AI 自动拆解为基地信息 + 原子活动积木
- **智能排产工作台**（`/planner`）
  - 从积木库拖拽编排
  - AI 按需求匹配基地并快速生成时间轴
- **文案导出工作台**（`/export`）
  - 基于排产时间轴级联生成 5 个章节
  - 导出为 `.docx`
- **积木资产管理**（`/library`）
  - 检索、查看与维护活动资产
- **管理后台**（`/admin/dashboard`）
  - 用户审计与基础管理（管理员权限）

### 1.2 五段式导出文案
系统会按以下结构生成课程方案：
1. 研学基地
2. 课程背景
3. 研学目标
4. 课程亮点
5. 研学流程（含时间轴表格）

---

## 2. 技术栈与架构

### 2.1 后端
- FastAPI + SQLAlchemy
- PostgreSQL
- OpenAI SDK（接入火山引擎 Ark 兼容接口）
- python-docx（Word 导出）

### 2.2 前端
- Vue 3 + Vite
- Vue Router（history 模式）
- Element Plus
- Axios

### 2.3 部署形态
- Docker Compose 三服务：
  - `db`（PostgreSQL）
  - `backend`（FastAPI，`8000`）
  - `frontend`（Nginx + SPA，`80`）
- Nginx 负责：
  - `/api/` 代理到后端
  - SPA fallback（`try_files ... /index.html`）

---

## 3. 目录结构

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py                 # API 入口
│   │   ├── models.py               # ORM 模型
│   │   ├── schemas.py              # Pydantic 模型
│   │   ├── services/
│   │   │   ├── ai_service.py       # AI 调用与章节生成
│   │   │   └── doc_service.py      # Word 渲染
│   │   └── utils/auth.py           # JWT 与密码加密
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── router/index.js
│   │   └── views/
│   │       ├── IngestView.vue
│   │       ├── Planner.vue
│   │       ├── ExportWorkbench.vue
│   │       └── ...
│   ├── nginx.conf
│   └── Dockerfile
└── docker-compose.yml
```

---

## 4. 快速启动（推荐：Docker Compose）

### 4.1 准备环境变量
在仓库根目录创建 `.env`：

```bash
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
POSTGRES_DB=study_tour_data

DATABASE_URL=postgresql://myuser:mypassword@db:5432/study_tour_data

ARK_API_KEY=your_ark_api_key
ARK_MODEL_ID=your_ark_model_id

APP_SECRET_KEY=replace_with_a_long_random_secret
```

> `APP_SECRET_KEY` 必填。未设置时后端会拒绝启动。

### 4.2 启动服务

```bash
docker compose up -d --build
```

### 4.3 访问地址
- 前端：`http://<server-ip>/`
- 后端 OpenAPI：`http://<server-ip>:8000/docs`

---

## 5. 本地开发

### 5.1 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL='postgresql://myuser:mypassword@localhost:5432/study_tour_data'
export APP_SECRET_KEY='your_secret'
export ARK_API_KEY='your_ark_key'
export ARK_MODEL_ID='your_model_id'

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5.2 前端

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

---

## 6. API 概览

- `POST /api/v1/auth/register` 用户注册
- `POST /api/v1/auth/login` 用户登录（返回 Bearer Token）
- `GET /api/v1/activities` 获取当前用户活动积木
- `POST /api/v1/activities` 创建活动积木
- `DELETE /api/v1/activities/{activity_id}` 删除活动积木
- `POST /api/v1/ai/mega-ingest` 原始文案 AI 分拣
- `POST /api/v1/planner/ai-arrange` AI 排产
- `GET /api/v1/locations/grouped` 按基地分组资产
- `POST /api/v1/export/word` 五段式文案导出 Word
- `GET /api/v1/admin/users` 管理员查看用户列表

---

## 7. 导出 Word 字体规范（重点）

当前导出规则：
- **文档题目 + 各级标题**：`方正小标宋简体`
- **正文 + 表格**：`仿宋`

> 注意：`.docx` 存储的是字体名称，不会打包字体文件本身。

你已将字体放在服务器：
- `/fzdbs.ttf`
- `/hwfs.ttf`

为了确保最终展示一致，需要在**生成/打开文档的环境**安装这两个字体（如 Linux 字体目录 + `fc-cache -fv`，或在 Windows Office 所在机器安装字体）。

---

## 8. 常见问题

### Q1: 打开页面只显示标题或刷新子路由 404？
请确认前端使用了 Nginx 配置并已启用：
- `/api/` 代理到 `backend:8000`
- `try_files $uri $uri/ /index.html`

### Q2: 导出成功但字体不对？
优先检查字体是否已安装到系统且字体名匹配：
- 方正小标宋简体
- 仿宋

### Q3: 登录后频繁 401 跳转？
确认请求头中 Bearer Token 正常、`APP_SECRET_KEY` 未变化，且前端/后端时间同步。

---

## 9. 安全与生产建议

- 将 CORS `allow_origins` 从 `*` 收敛到你的域名
- 通过 HTTPS 暴露服务
- 定期轮换 `APP_SECRET_KEY`
- 对 AI 接口增加速率限制与审计日志
- 为数据库启用定期备份

---

## 10. License

内部项目，默认不对外开源许可；如需开放请补充 LICENSE 文件。
