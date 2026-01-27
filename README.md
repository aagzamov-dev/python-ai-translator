# 🇨🇳 → 🌍 Chinese Translation API

A powerful Python API for translating Chinese text in JSON data to **Uzbek**, **Russian**, or **English** using **DeepSeek AI**.

## ✨ Features

- **🎯 Natural Translations**: Human-like, fluent output (not word-for-word literal translations)
- **📝 Smart Summarization**: Automatically condenses verbose Chinese text
- **🔄 Recursive Translation**: Handles deeply nested JSON structures
- **🎛️ Selective Translation**: Choose specific keys to translate
- **⚡ Batch Processing**: Translate multiple items in one request
- **📖 Interactive Docs**: Swagger UI included

## 🌐 Supported Languages

| Code | Language | Native Name |
|------|----------|-------------|
| `uz` | Uzbek | O'zbek tili |
| `ru` | Russian | Русский |
| `en` | English | English |

## 🚀 Installation

### 1. Create a virtual environment

```bash
python -m venv .venv
```

### 2. Activate the virtual environment

**Windows:**
```bash
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` and add your **DeepSeek API key**:

```env
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here
```

## 🏃 Running the API

```bash
python run.py
```

The server will start at `http://localhost:8000`

## 📖 API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔌 API Endpoints

### `POST /translate` - Translate JSON

Translate Chinese text values in a JSON object.

**Request:**
```json
{
    "data": {
        "product_name": "高品质蓝牙耳机",
        "description": "这款无线蓝牙耳机采用最新降噪技术，音质清晰，佩戴舒适，电池续航长达20小时。",
        "price": 299
    },
    "target_language": "ru"
}
```

**Response:**
```json
{
    "success": true,
    "translated_data": {
        "product_name": "Высококачественные Bluetooth наушники",
        "description": "Беспроводные наушники с шумоподавлением, чистым звуком и 20-часовой работой от батареи.",
        "price": 299
    },
    "target_language": "ru",
    "summarized": false,
    "tokens_used": 185
}
```

### `POST /translate/batch` - Batch Translate

Translate multiple JSON objects at once.

**Request:**
```json
{
    "items": [
        {"name": "智能手表", "desc": "支持心率监测和睡眠追踪"},
        {"name": "无线充电器", "desc": "快速充电15W，兼容多种设备"}
    ],
    "target_language": "uz"
}
```

### `GET /translate/simple` - Quick Translation

Simple GET endpoint for testing.

```
GET /translate/simple?text=你好世界&lang=en
```

**Response:**
```json
{
    "success": true,
    "translated_data": {
        "text": "Hello World"
    },
    "target_language": "en"
}
```

### `GET /languages` - Supported Languages

Get list of supported languages and features.

## ⚙️ Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `DEEPSEEK_API_KEY` | Your DeepSeek API key | **Required** |
| `DEEPSEEK_BASE_URL` | DeepSeek API base URL | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | Model to use | `deepseek-chat` |
| `MAX_TOKENS` | Maximum tokens per request | `4096` |
| `TEMPERATURE` | Model temperature (0-1) | `0.5` |
| `ENABLE_SUMMARIZATION` | Auto-summarize long texts | `true` |
| `SUMMARIZE_THRESHOLD` | Character count to trigger summarization | `500` |

## 📝 Example Use Cases

### E-commerce Product Translation

Translate product information from Chinese suppliers:

```bash
curl -X POST "http://localhost:8000/translate" \
     -H "Content-Type: application/json" \
     -d '{
           "data": {
             "title": "新款夏季连衣裙女装",
             "material": "100%纯棉",
             "size": ["S", "M", "L", "XL"],
             "description": "清凉舒适的夏季连衣裙，适合各种场合穿着。"
           },
           "target_language": "uz"
         }'
```

### With Summarization

Force summarization for verbose text:

```bash
curl -X POST "http://localhost:8000/translate" \
     -H "Content-Type: application/json" \
     -d '{
           "data": {
             "details": "这是一段非常长的中文产品描述，包含了很多重复的信息和营销话术..."
           },
           "target_language": "en",
           "summarize": true
         }'
```

### Selective Key Translation

Only translate specific keys:

```bash
curl -X POST "http://localhost:8000/translate" \
     -H "Content-Type: application/json" \
     -d '{
           "data": {
             "name": "电子产品",
             "sku": "PROD-12345",
             "description": "高品质电子产品"
           },
           "target_language": "ru",
           "keys_to_translate": ["name", "description"]
         }'
```

## 🔑 Getting a DeepSeek API Key

1. Visit [DeepSeek Platform](https://platform.deepseek.com/)
2. Create an account or sign in
3. Navigate to API Keys section
4. Generate a new API key
5. Add it to your `.env` file

## 📄 License

MIT License
# python-ai-translator
