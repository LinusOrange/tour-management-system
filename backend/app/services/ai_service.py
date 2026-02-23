import json
import os
import re
from openai import OpenAI
from typing import Optional, Dict, List, Set

# 配置信息
AI_KEY = os.getenv("ARK_API_KEY", "91a598f5-a30c-4ac7-9c6f-3e0496b73c3b")
AI_URL = "https://ark.cn-beijing.volces.com/api/v3"
AI_MODEL = os.getenv("ARK_MODEL_ID", "ep-20260215114801-j76jf") 

client = OpenAI(api_key=AI_KEY, base_url=AI_URL)

# --- 1. 定义结构化 Schema ---

# 用于“联网搜索”补全基地的 Schema
LOCATION_INFO_SCHEMA = {
    "name": "location_info_retrieval",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "address": {"type": "string"},
            "description": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}},
            "coordinates": {
                "type": "object",
                "properties": {
                    "lng": {"type": "number"},
                    "lat": {"type": "number"}
                },
                "required": ["lng", "lat"],
                "additionalProperties": False
            }
        },
        "required": ["name", "address", "description", "tags", "coordinates"],
        "additionalProperties": False
    }
}

# 用于“AI 分拣入库”的 Schema
INGEST_SCHEMA = {
    "name": "study_tour_ingest",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "address": {"type": "string"},
                    "description": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "coordinates": {
                        "type": "object",
                        "properties": {
                            "lng": {"type": "number"},
                            "lat": {"type": "number"}
                        },
                        "required": ["lng", "lat"],
                        "additionalProperties": False
                    }
                },
                "required": ["name", "address", "description", "tags", "coordinates"],
                "additionalProperties": False
            },
            "activities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "duration": {"type": "integer"},
                        "content": {"type": "string"},
                        "edu_goals": {"type": "object", "additionalProperties": {"type": "string"}},
                        "cost_metadata": {
                            "type": "object",
                            "properties": {
                                "ticket": {"type": "number"},
                                "material": {"type": "number"}
                            },
                            "required": ["ticket", "material"],
                            "additionalProperties": False
                        }
                    },
                    "required": ["title", "duration", "content", "edu_goals", "cost_metadata"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["location", "activities"],
        "additionalProperties": False
    }
}

# --- 2. 核心业务函数 ---

def search_and_summarize_location(location_name: str) -> Optional[Dict]:
    """联网搜索基地信息"""
    try:
        response = client.chat.completions.create(
            model=AI_MODEL, 
            messages=[
                {"role": "system", "content": "你是一个资深的研学基地调研员。"},
                {"role": "user", "content": f"请联网搜索位于西安或周边的基地信息：{location_name},要求：1. description 字段必须扩充至 500 字左右。2. 内容需包含:基地的历史背景、在国家科研体系中的地位、核心研学设施以及具体的教育意义。3. 语言风格要专业且具有科技感。"}
            ],
            response_format={"type": "json_schema", "json_schema": LOCATION_INFO_SCHEMA}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"📡 联网搜索失败: {e}")
        return None

def analyze_mega_text(raw_text: str) -> Optional[Dict]:
    """AI 分拣：文案转积木"""
    try:
        response = client.chat.completions.create(
            model=AI_MODEL, 
            messages=[
                {"role": "system", "content": "你是一个资深的研学资源录入员。"},
                {"role": "user", "content": f"请拆解这段内容：\n{raw_text}"}
            ],
            response_format={"type": "json_schema", "json_schema": INGEST_SCHEMA}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Mega Ingest Schema Error: {e}")
        return None

def plan_activities_with_ai(requirement: str, activity_pool: list) -> list:
    """AI 排产：筛选 ID"""
    pool_text = "\n".join([f"- ID: {a['id']}, 标题: {a['title']}" for a in activity_pool])
    try:
        response = client.chat.completions.create(
            model=AI_MODEL, 
            messages=[
                {"role": "system", "content": "你是一个行程规划专家。"},
                {"role": "user", "content": f"需求：{requirement}\n池：\n{pool_text}"}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "plan_result",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "selected_ids": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["selected_ids"],
                        "additionalProperties": False
                    }
                }
            }
        )
        result = json.loads(response.choices[0].message.content)
        return result.get("selected_ids", []) 
    except Exception as e:
        print(f"Planning Schema Error: {e}")
        return []

def _extract_keywords(text: str) -> List[str]:
    """从自然语言需求中提取可用于匹配的关键词（中英文、数字）。"""
    if not text:
        return []

    tokens = re.split(r"[，。,.；;、\s:：()（）\[\]【】|/\\-]+", text.lower())
    stop_words = {
        "我", "我们", "你", "你们", "请", "需要", "想要", "安排", "一个", "一些", "进行", "可以", "以及", "和", "与", "的", "在", "到", "去", "并", "含", "包含", "相关", "主题", "活动", "课程", "研学", "行程", "天", "日"
    }
    keywords = [t for t in tokens if t and len(t) >= 2 and t not in stop_words]
    return list(dict.fromkeys(keywords))


def select_multiple_locations_with_ai(requirement: str, locations_pool: list) -> list:
    """
    AI+规则混合匹配基地：
    1) 规则：关键词命中基地名称 / 基地摘要（含子活动标题、内容、目标）
    2) AI：语义匹配补充候选
    3) 合并去重
    """
    if not requirement or not locations_pool:
        return []

    # 规则匹配：支持“基地名称命中” + “活动目标/内容命中”
    keywords = _extract_keywords(requirement)
    keyword_matched: Set[str] = set()
    for loc in locations_pool:
        name_text = str(loc.get('name', '')).lower()
        summary_text = str(loc.get('summary', '')).lower()
        if any((kw in name_text) or (kw in summary_text) for kw in keywords):
            keyword_matched.add(loc.get('name'))

    # AI 匹配：用于补充语义相关基地
    pool_text = "\n".join([
        f"- 基地名: {loc.get('name', '')}\n  基地摘要: {loc.get('summary', '')}" for loc in locations_pool
    ])
    ai_matched: Set[str] = set()
    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "你是研学排产匹配专家。必须根据用户需求关键词匹配基地。若关键词命中基地名称或基地下任一子活动目标/内容/标题，则应选择该基地。"
                },
                {
                    "role": "user",
                    "content": f"用户需求：{requirement}\n\n候选基地与子活动摘要：\n{pool_text}\n\n请返回最相关的基地名称数组。"
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "location_selection",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "selected_locations": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["selected_locations"],
                        "additionalProperties": False
                    }
                }
            }
        )
        res_data = json.loads(response.choices[0].message.content)
        ai_matched = set(res_data.get("selected_locations", []))
    except Exception as e:
        print(f"Selection Schema Error: {e}")

    merged = list(dict.fromkeys([*keyword_matched, *ai_matched]))

    # 如果完全没命中，保底给 AI 第一候选（避免空计划）
    if not merged and locations_pool:
        merged = [locations_pool[0].get('name')]

    return merged
    
def generate_document_sections(location_data: dict, activities: list, custom_prompts: dict = None) -> dict:
    """
    分段生成逻辑：加入用户自定义提示词增强
    """
    base_info = location_data.get('description', '')
    act_titles = "、".join([a['title'] for a in activities])
    sections = {}
    
    # 定义生成配置：标题、Key、默认 Prompt
    config = [
        ('background', '课程背景', f"写一段 800 字的课程背景。基地：{base_info[:300]}"),
        ('goals', '研学目标', f"基于活动 {act_titles}，生成 500 字的研学目标。"),
        ('highlights', '课程亮点', f"总结 4 个硬核课程亮点，每个亮点带标题并展开。")
    ]

    for key, title, default_p in config:
        # 如果用户输入了自定义提示词，则将其注入
        user_instr = custom_prompts.get(key, "") if custom_prompts else ""
        final_prompt = f"系统要求：{default_p}\n用户特别指令：{user_instr}\n请开始撰写："
        
        print(f"正在生成 {title}...")
        sections[key] = call_ark_simple(final_prompt)
    
    return sections

def call_ark_simple(prompt: str) -> str:
    """内部辅助：快速获取 AI 文本"""
    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except:
        return "内容生成失败，请手动补充。"

def generate_export_sections(plan_context: dict, custom_prompts: dict | None = None) -> dict:
    """
    级联生成导出文案 5 个章节。
    - section_1_base: 研学基地（结合排产工作台的基地/活动）
    - section_2_background: 课程背景
    - section_3_goals: 研学目标
    - section_4_highlights: 课程亮点
    - section_5_process: 研学流程说明
    """
    custom_prompts = custom_prompts or {}

    locations = plan_context.get('locations', [])
    timeline = plan_context.get('timeline', [])
    requirement = plan_context.get('requirement', '')

    location_text = "\n".join([
        f"- 基地：{loc.get('name','未知基地')}；地址：{loc.get('address','待补充')}；简介：{loc.get('description','待补充')}"
        for loc in locations
    ])

    timeline_text = "\n".join([
        f"- {idx+1}. [{item.get('display_time','时间待定')}] {item.get('title','未命名活动')}（{item.get('duration', 0)}分钟，基地：{item.get('location_name','待定')}）"
        for idx, item in enumerate(timeline)
    ])

    section_configs = [
        (
            'section_1_base',
            '研学基地',
            f"请根据以下排产涉及基地信息，撰写 400~600 字『研学基地』章节。重点写基地特色、教育价值与课程适配性。\n基地信息：\n{location_text}"
        ),
        (
            'section_2_background',
            '课程背景',
            f"请撰写 500~800 字『课程背景』。结合用户需求与基地定位，说明项目缘起、时代价值、学段意义。\n用户需求：{requirement}\n基地信息：\n{location_text}"
        ),
        (
            'section_3_goals',
            '研学目标',
            f"请生成『研学目标』章节，按知识目标、能力目标、素养目标三个维度展开，每个维度 2-3 条，可执行可评价。\n行程活动：\n{timeline_text}"
        ),
        (
            'section_4_highlights',
            '课程亮点',
            "请生成『课程亮点』章节，输出 4 个亮点，每个亮点包含标题和一段 120~180 字说明，强调创新性与可落地性。"
        ),
        (
            'section_5_process',
            '研学流程',
            f"请根据以下时间轴，写一段 400~700 字『研学流程说明』，强调环节衔接与学习闭环。\n时间轴：\n{timeline_text}"
        )
    ]

    generated = {}
    for key, section_name, default_prompt in section_configs:
        user_prompt = custom_prompts.get(key, '').strip()
        final_prompt = (
            "你是一名资深研学课程总设计师，请用正式中文输出，不要使用Markdown。\n"
            f"章节：{section_name}\n"
            f"基础要求：{default_prompt}\n"
            f"用户额外要求：{user_prompt if user_prompt else '无'}\n"
            "请直接给出可放入方案书的正文。"
        )

        print(f"正在生成导出章节：{section_name}...")
        generated[key] = call_ark_simple(final_prompt)

    return generated
