import time
import os
from typing import List, Optional, Dict
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from pydantic import BaseModel
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer

# 核心导入
from app import models, schemas, database
from app.database import engine, get_db
from app.services import ai_service
from app.utils import auth as auth_utils

from fastapi.responses import StreamingResponse
from app.services import doc_service

# --- 1. 鉴权配置 ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="认证已过期或无效，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth_utils.SECRET_KEY, algorithms=[auth_utils.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

# --- 2. 数据库与应用初始化 ---
def init_db():
    retries = 5
    while retries > 0:
        try:
            models.Base.metadata.create_all(bind=engine)
            print("🚀 数据库已连接，表结构已同步!")
            break
        except OperationalError:
            retries -= 1
            print(f"⚠️ 数据库未就绪，重试中... ({5 - retries}/5)")
            time.sleep(2)

init_db()
app = FastAPI(title="研学原子积木系统 - 多用户联网增强版")

# main.py 修改处
origins = [
    "http://212.64.26.173",  # 👈 新服务器 IP
    "http://chengdx.art",
    "http://localhost:5173",
]

# CORS 配置
# 针对你提到的 CORS 报错，建议生产环境将 ["*"] 替换为 ["http://chengdx.art"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. Pydantic 模型 ---
class UserAuth(BaseModel):
    username: str
    password: str

class PlanningRequest(BaseModel):
    requirement: str

class ActivityCreate(BaseModel):
    title: str
    duration: int
    content: str
    location_name: str

# --- 4. [新增] 联网补全核心逻辑 ---

def ensure_location_with_search(location_name: str, db: Session, user_id: UUID) -> models.Location:
    """
    逻辑：检查本地库 -> 若无记录则联网搜索补全 -> 持久化
    """
    # 1. 检查本地数据库
    db_location = db.query(models.Location).filter(
        models.Location.name == location_name,
        models.Location.owner_id == user_id
    ).first()

    if db_location:
        return db_location

    # 2. 本地缺失，触发联网搜索 (调用 ai_service 中的新函数)
    print(f"📡 本地未发现基地【{location_name}】，启动 AI 联网检索补全...")
    ai_data = ai_service.search_and_summarize_location(location_name)

    if ai_data:
        new_loc = models.Location(
            name=location_name,
            address=ai_data.get("address", "待核实"),
            description=ai_data.get("description", "暂无介绍"),
            tags=ai_data.get("tags", []),
            owner_id=user_id
        )
    else:
        # 兜底：AI 搜索也未命中，创建基础记录
        new_loc = models.Location(
            name=location_name,
            owner_id=user_id,
            address="搜索未果，请手动补充地址",
            description="暂无"
        )

    db.add(new_loc)
    db.flush() 
    return new_loc

# --- 5. 身份认证接口 ---

@app.post("/api/v1/auth/register")
def register(user: UserAuth, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已被占用")
    
    new_user = models.User(
        username=user.username,
        hashed_password=auth_utils.hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    try:
        create_demo_data(new_user.id, db)
    except Exception as e:
        print(f"演示数据生成失败: {e}")
    
    return {"status": "success", "message": "注册成功，已为您初始化演示资产"}

def create_demo_data(user_id: UUID, db: Session):
    demo_location = models.Location(
        name="青岛研学科技馆（演示）",
        address="青岛市黄岛区科教路1号",
        owner_id=user_id
    )
    db.add(demo_location)
    db.flush()

    demo_activities = [
        {"title": "【演示】雷达信号处理讲座", "duration": 90, "content": "了解SAR成像基本原理。"},
        {"title": "【演示】无人机组装实操", "duration": 120, "content": "组装并测试飞行稳定性。"}
    ]
    for act in demo_activities:
        db.add(models.AtomicActivity(
            title=act["title"], duration=act["duration"], content=act["content"],
            location_id=demo_location.id, owner_id=user_id
        ))
    db.commit()

@app.post("/api/v1/auth/login")
def login(user: UserAuth, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not auth_utils.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    access_token = auth_utils.create_access_token(data={"sub": str(db_user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

# --- 6. 业务接口 ---

@app.get("/api/v1/activities")
def get_user_activities(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    activities = db.query(models.AtomicActivity).filter(models.AtomicActivity.owner_id == current_user.id).all()
    return [{
        "id": str(a.id),
        "title": a.title,
        "duration": a.duration,
        "content": a.content,
        "location_name": a.location.name if a.location else "未知",
        # --- 新增以下字段 ---
        "location_address": a.location.address if a.location else "",
        "location_description": a.location.description if a.location else "暂无介绍",
        "location_tags": a.location.tags if a.location else []
    } for a in activities]

@app.post("/api/v1/activities")
async def create_activity(activity: ActivityCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # 使用联网搜索补全逻辑
    target_location = ensure_location_with_search(activity.location_name, db, current_user.id)

    new_act = models.AtomicActivity(
        title=activity.title,
        duration=activity.duration,
        content=activity.content,
        location_id=target_location.id,
        owner_id=current_user.id
    )
    db.add(new_act)
    db.commit()
    return {"status": "success", "id": str(new_act.id)}

@app.delete("/api/v1/activities/{activity_id}")
def delete_activity(activity_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db.query(models.AtomicActivity).filter(
        models.AtomicActivity.id == activity_id,
        models.AtomicActivity.owner_id == current_user.id
    ).delete()
    db.commit()
    return {"status": "deleted"}

@app.post("/api/v1/ai/mega-ingest")
async def mega_ingest(request: schemas.MegaIngestRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    data = ai_service.analyze_mega_text(request.raw_text)
    if not data:
        raise HTTPException(status_code=500, detail="AI 解析失败")

    # 基地处理：优先查重与联网补全
    db_location = ensure_location_with_search(data['location']['name'], db, current_user.id)

    # 活动处理
    for act_data in data['activities']:
        db_act = models.AtomicActivity(
            location_id=db_location.id, 
            owner_id=current_user.id, 
            **act_data
        )
        db.add(db_act)
    db.commit()

    return {"status": "success", "location": data['location'], "activities": data['activities']}

@app.post("/api/v1/planner/ai-arrange")
async def ai_arrange_itinerary(req: PlanningRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    all_acts = db.query(models.AtomicActivity).filter(models.AtomicActivity.owner_id == current_user.id).all()
    loc_map = {}
    for a in all_acts:
        name = a.location.name if a.location else "通用"
        if name not in loc_map: loc_map[name] = []
        loc_map[name].append(a)

    locations_pool = [{"name": n, "summary": "、".join([act.title for act in acts])} for n, acts in loc_map.items()]
    selected_names = ai_service.select_multiple_locations_with_ai(req.requirement, locations_pool)

    final_plan = []
    for name in selected_names:
        if name in loc_map:
            for act in loc_map[name]:
                final_plan.append({"id": str(act.id), "title": act.title, "duration": act.duration, "location_name": name})

    return {"plan": final_plan, "matched_bases": selected_names}

@app.get("/api/v1/admin/users")
def get_all_users(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="权限不足")
    users = db.query(models.User).all()
    return [{"id": str(u.id), "username": u.username, "is_admin": u.is_admin,
             "activity_count": db.query(models.AtomicActivity).filter_by(owner_id=u.id).count()} for u in users]
            
@app.get("/api/v1/locations/grouped")
def get_grouped_assets(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """按基地分组查询所有资产"""
    locations = db.query(models.Location).filter(models.Location.owner_id == current_user.id).all()
    
    result = []
    for loc in locations:
        result.append({
            "id": str(loc.id),
            "name": loc.name,
            "address": loc.address,
            "description": loc.description,
            "tags": loc.tags,
            # 嵌套该基地下的所有原子积木
            "activities": [{
                "id": str(a.id),
                "title": a.title,
                "duration": a.duration,
                "content": a.content
            } for a in loc.activities]
        })
    return result


class ExportTimelineItem(BaseModel):
    id: Optional[str] = None
    title: str
    duration: int
    location_name: Optional[str] = None
    display_time: Optional[str] = None


class ExportRequest(BaseModel):
    requirement: Optional[str] = ""
    timeline: List[ExportTimelineItem]
    custom_prompts: Dict[str, str]


@app.post("/api/v1/export/word")
async def export_itinerary_word(
    req: ExportRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not req.timeline:
        raise HTTPException(status_code=400, detail="时间轴为空，请先在排产工作台添加活动")

    activity_ids = [item.id for item in req.timeline if item.id]
    db_activities = []
    if activity_ids:
        db_activities = db.query(models.AtomicActivity).filter(
            models.AtomicActivity.id.in_(activity_ids),
            models.AtomicActivity.owner_id == current_user.id
        ).all()

    activities_by_id = {str(a.id): a for a in db_activities}

    unique_locations = {}
    for item in req.timeline:
        db_act = activities_by_id.get(item.id) if item.id else None
        loc_name = item.location_name or (db_act.location.name if db_act and db_act.location else "未命名基地")
        if loc_name in unique_locations:
            continue

        unique_locations[loc_name] = {
            "name": loc_name,
            "address": (db_act.location.address if db_act and db_act.location else "待补充"),
            "description": (db_act.location.description if db_act and db_act.location else "该基地暂无详细介绍，请后续补充。")
        }

    timeline_data = []
    for item in req.timeline:
        db_act = activities_by_id.get(item.id) if item.id else None
        timeline_data.append({
            "title": item.title,
            "duration": item.duration,
            "location_name": item.location_name or (db_act.location.name if db_act and db_act.location else "待定基地"),
            "display_time": item.display_time or "时间待定"
        })

    plan_context = {
        "requirement": req.requirement or "",
        "locations": list(unique_locations.values()),
        "timeline": timeline_data
    }

    ai_sections = ai_service.generate_export_sections(
        plan_context=plan_context,
        custom_prompts=req.custom_prompts
    )

    final_data = {
        "title": "研学课程方案",
        "locations": list(unique_locations.values()),
        "timeline": timeline_data,
        "ai_sections": ai_sections
    }

    file_stream = doc_service.create_study_tour_docx(final_data)

    return StreamingResponse(
        file_stream,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=study-tour-program.docx"}
    )

