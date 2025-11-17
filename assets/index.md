# Hearts Echo

將你的日常記錄轉換成自然語言描述。

## API 使用方式

**端點:** `POST /echo`

**輸入範例:**
```json
{
  "clothe": "white T-shirt",
  "weather": "sunny",
  "mood": "happy",
  "date": "2025/11/17"
}
```

**輸出範例:**
```json
{
  "text": "On a sunny day, you happily put on a white T-shirt.",
  "used": ["clothe", "weather", "mood"],
  "ignore": ["date"]
}
```

**說明:**
- API 會使用 `clothe`、`weather`、`mood` 生成描述
- `date` 欄位會被忽略
- 回傳生成的文字和欄位使用情況

## 完整文檔
訪問 [/docs](/docs) 查看互動式 API 文檔
