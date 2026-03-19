import { SkillHandler, ToolCallResult } from "@anthropic-ai/sdk";

interface SummarizeConversationParams {
  chatList: string;
  historySummary?: string;
}

interface SummaryResponse {
  code: number;
  message: string;
  data?: {
    summary: string;
  };
}

const SUMMARY_API_URL =
  "https://iautomark.sdm.qq.com/assistant-analyse/v1/assistant/poc/summary/trigger";

async function summarizeConversation(
  params: SummarizeConversationParams
): Promise<ToolCallResult> {
  const { chatList, historySummary = "" } = params;

  if (!chatList || chatList.trim() === "") {
    return {
      success: false,
      error: "chatList 参数不能为空，请提供对话内容",
    };
  }

  try {
    const response = await fetch(SUMMARY_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        chatList,
        historySummary,
      }),
    });

    if (!response.ok) {
      return {
        success: false,
        error: `API 请求失败: HTTP ${response.status} ${response.statusText}`,
      };
    }

    const result: SummaryResponse = await response.json();

    if (result.code !== 0) {
      return {
        success: false,
        error: `会话小结生成失败: ${result.message}`,
      };
    }

    return {
      success: true,
      data: {
        summary: result.data?.summary || "无法生成摘要",
        message: "会话小结生成成功",
      },
    };
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : "未知错误";
    return {
      success: false,
      error: `请求会话小结接口时发生错误: ${errorMessage}`,
    };
  }
}

export const handler: SkillHandler = {
  async handleToolCall(toolName: string, params: Record<string, unknown>) {
    switch (toolName) {
      case "summarize_conversation":
        return summarizeConversation(params as SummarizeConversationParams);
      default:
        return {
          success: false,
          error: `未知的工具: ${toolName}`,
        };
    }
  },
};

export default handler;
