import json
import os
from openai import OpenAI
from typing import Optional, Dict

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

def select_multiple_locations_with_ai(requirement: str, locations_pool: list) -> list:
    """AI 匹配：筛选基地名称"""
    pool_text = "\n".join([f"- {loc['name']}: {loc['summary']}" for loc in locations_pool])
    try:
        response = client.chat.completions.create(
            model=AI_MODEL, 
            messages=[
                {"role": "system", "content": "你是一个研学匹配专家。"},
                {"role": "user", "content": f"需求：{requirement}\n资源：\n{pool_text}"}
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
        return res_data.get("selected_locations", [])
    except Exception as e:
        print(f"Selection Schema Error: {e}")
        return []
    
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