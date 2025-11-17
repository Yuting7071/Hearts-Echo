from enum import Enum
from functools import cache
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Tuple
import uvicorn
import markdown
from pathlib import Path
import random
import re

app = FastAPI(title="Hearts Echo API", version="1.0.0")

# 定義輸入模型
class EchoInput(BaseModel):
    clothe: Optional[str] = None
    weather: Optional[str] = None
    mood: Optional[str] = None
    date: Optional[str] = None

# 定義輸出模型
class EchoOutput(BaseModel):
    text: str
    used: List[str]
    ignore: List[str]

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@cache
def load_index_html() -> str:
    # 讀取 Markdown 文件
    md_file = Path("assets/index.md")
    md_content = md_file.read_text(encoding="utf-8")
    return f"""
    <!DOCTYPE html>
    <html lang="en-US">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Hearts Echo</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                line-height: 1.6;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                color: #333;
            }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; margin-top: 30px; }}
            code {{
                background-color: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
            }}
        </style>
    </head>
    <body>
        {markdown.markdown(md_content, extensions=['extra', 'codehilite'])}
    </body>
    </html>
    """

@app.get("/", response_class=HTMLResponse)
async def root():
    return load_index_html()

@app.post("/echo", response_model=EchoOutput)
async def echo(data: EchoInput):
    """
    接收包含服裝、天氣、心情和日期的資料,生成自然語言描述。
    會使用 clothe, weather, mood 這些欄位，並忽略 date。
    """
    
    # 生成自然語言描述
    text, used_fields, ignored_fields = generate_description(data.model_dump(exclude_none=False))
    
    return EchoOutput(
        text=text,
        used=used_fields,
        ignore=ignored_fields
    )

@cache
def load_templates() -> Tuple[List[str], List[str], List[Tuple[str, List[str]]]]:
    """
    載入句子模板並解析參數
    回傳格式: (使用欄位列表, 未使用欄位列表, [(模板字串, [參數列表]), ...])
    """
    template_file = Path("assets/templates.txt")
    content = template_file.read_text(encoding="utf-8")
    templates = []
    fields_to_use = []
    fields_to_ignore = []
    
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # 解析 used 和 unused 定義
        if line.startswith("used:"):
            fields_to_use = [f.strip() for f in line.replace("used:", "").split(",")]
        elif line.startswith("unused:"):
            fields_to_ignore = [f.strip() for f in line.replace("unused:", "").split(",")]
        else:
            # 使用正則表達式找出所有 {參數名} 格式的參數
            params = re.findall(r'\{(\w+)\}', line)
            templates.append((line, params))
    
    return fields_to_use, fields_to_ignore, templates

def generate_description(data: dict) -> Tuple[str, List[str], List[str]]:
    """
    根據提供的資料生成自然語言描述
    會讀取範本，解析所需參數，並根據輸入資料篩選可用範本
    參數越多的範本加權越高
    
    回傳: (描述文字, 使用的欄位列表, 忽略的欄位列表)
    """
    # 從範本檔案載入欄位定義
    fields_to_use, fields_to_ignore, all_templates = load_templates()
    
    # 收集有值且會使用的欄位
    available_data = {}
    used_fields = []
    for field in fields_to_use:
        if field in data and data[field]:
            used_fields.append(field)
            available_data[field] = data[field]
    
    # 收集有值但會忽略的欄位
    ignored_fields = []
    for field in fields_to_ignore:
        if field in data and data[field]:
            ignored_fields.append(field)
    
    if not available_data:
        return "No information provided.", used_fields, ignored_fields
    
    # 篩選出可以滿足的範本
    valid_templates = []
    weights = []
    for template_str, required_params in all_templates:
        # 檢查是否所有必需參數都存在且有值
        if all(param in available_data and available_data[param] for param in required_params):
            weight = len(required_params) ** 2  # 參數數量的平方作為權重
            valid_templates.append((template_str, required_params))
            weights.append(weight)
    
    # 如果有滿足條件的範本,根據權重隨機選擇一個
    if valid_templates:
        template_str, params = random.choices(valid_templates, weights=weights, k=1)[0]
        return template_str.format(**available_data), used_fields, ignored_fields
    
    # 如果沒有滿足條件的範本，回傳預設訊息
    return "Failed to generate description with the provided information.", used_fields, ignored_fields

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
