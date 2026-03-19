# Conversation Summary Skill

会话小结 OpenClaw Skill，用于对对话内容进行摘要生成。

## 功能

- 输入对话内容，自动生成会话小结
- 支持历史摘要增量更新

## 安装

```bash
cd conversation-summary
npm install
npm run build
```

## 工具

### summarize_conversation

对对话内容进行小结，生成会话摘要。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| chatList | string | 是 | 对话内容列表，JSON 格式 |
| historySummary | string | 否 | 历史会话摘要，用于增量更新 |

**使用示例：**

```json
{
  "chatList": "[{\"role\":\"user\",\"content\":\"今天天气怎么样？\"},{\"role\":\"assistant\",\"content\":\"今天天气晴朗，气温25度。\"}]",
  "historySummary": ""
}
```

**返回示例：**

```json
{
  "success": true,
  "data": {
    "summary": "用户询问了天气情况，助手回复今天天气晴朗，气温25度。",
    "message": "会话小结生成成功"
  }
}
```

## API

调用接口：`https://iautomark.sdm.qq.com/assistant-analyse/v1/assistant/poc/summary/trigger`

请求方式：POST

请求体：
```json
{
  "chatList": "对话内容",
  "historySummary": "历史摘要"
}
```
