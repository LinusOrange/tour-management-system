from datetime import datetime, timedelta
from app import models
from app.services import amap_service
from datetime import datetime, timedelta

class PlanningAgent:
    def __init__(self, db, ai_client):
        self.db = db
        self.ai = ai_client

    def arrange(self, location_id, user_request, start_time_str="09:00"):
        """
        核心排产逻辑
        user_request: "我想要一个包含漆扇和手工的行程，节奏不要太快"
        """
        # 1. 获取该地点下所有的积木库
        all_activities = self.db.query(models.AtomicActivity).filter(
            models.AtomicActivity.location_id == location_id
        ).all()
        
        activity_list_text = "\n".join([f"- {a.title} (时长:{a.duration}分钟, ID:{a.id})" for a in all_activities])

        # 2. 调用 AI 进行“智能筛选与排序”
        prompt = f"""
        用户要求：{user_request}
        现有积木库：
        {activity_list_text}
        
        请从中挑选出最符合要求的积木，并按逻辑顺序排列。
        仅返回一个 ID 列表，格式如：["id1", "id2"]
        """
        # (此处省略 AI 调用逻辑，假设返回了 selected_ids)
        selected_ids = self.call_ai_for_ids(prompt) 

        # 3. 时间链计算
        current_time = datetime.strptime(start_time_str, "%H:%M")
        itinerary_plan = []
        
        for idx, aid in enumerate(selected_ids):
            act = next(a for a in all_activities if str(a.id) == aid)
            itinerary_plan.append({
                "time": current_time.strftime("%H:%M"),
                "activity": act.title,
                "duration": act.duration
            })
            # 自动累加时长，生成下一个活动的时间点
            current_time += timedelta(minutes=act.duration + 15) # 默认预留15分钟转场
            
        return itinerary_plan
    
class SmartPlanner:
    def __init__(self, db):
        self.db = db

    async def generate_itinerary(self, activity_ids: list, start_time_str: str):
        current_time = datetime.strptime(start_time_str, "%H:%M")
        final_itinerary = []
        last_location_coords = None

        for act_id in activity_ids:
            # 1. 从数据库读取活动及其地点坐标
            activity = self.db.query(models.AtomicActivity).get(act_id)
            location = activity.location
            current_coords = f"{location.coordinates['lng']},{location.coordinates['lat']}"

            # 2. 如果换了地点，计算车程并插入“交通积木”
            if last_location_coords and last_location_coords != current_coords:
                drive_time = await amap_service.get_driving_duration(
                    last_location_coords, current_coords
                )
                
                final_itinerary.append({
                    "type": "TRANSPORT",
                    "title": f"行驶至 {location.name}",
                    "start": current_time.strftime("%H:%M"),
                    "duration": drive_time
                })
                current_time += timedelta(minutes=drive_time)

            # 3. 插入活动积木
            final_itinerary.append({
                "type": "ACTIVITY",
                "title": activity.title,
                "start": current_time.strftime("%H:%M"),
                "duration": activity.duration,
                "location": location.name
            })
            
            # 更新当前时间和最后坐标
            current_time += timedelta(minutes=activity.duration)
            last_location_coords = current_coords

        return final_itinerary