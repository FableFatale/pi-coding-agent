/**
 * Context Compressor - 上下文压缩机制
 * 
 * 当会话消息达到阈值时自动触发压缩
 * 保护：前3条（系统设定）+ 后20条（最近上下文）
 * 中间：LLM 总结
 */

export interface CompressionConfig {
  thresholdPercent: number;  // 触发阈值，默认 0.5 (50%)
  protectFirst: number;      // 保护前N条，默认 3
  protectLast: number;       // 保护后N条，默认 20
  summaryPrefix: string;      // 总结前缀模板
}

export const DEFAULT_CONFIG: CompressionConfig = {
  thresholdPercent: 0.5,
  protectFirst: 3,
  protectLast: 20,
  summaryPrefix: "[压缩上下文 - 省略了 {count} 条消息]"
};

export interface CompressionResult {
  original: number;
  compressed: number;
  summary: string;
  preserved: { role: string; content: string }[];
  removed: { role: string; content: string }[];
}

/**
 * ContextCompressor
 * 
 * 压缩策略：
 * 1. 检查消息数量是否超过阈值
 * 2. 保留前3条（系统设定）
 * 3. 保留后20条（最近上下文）
 * 4. 中间部分用 LLM 总结
 */
export class ContextCompressor {
  private config: CompressionConfig;
  private maxMessages: number;

  constructor(config: Partial<CompressionConfig> = {}, maxMessages: number = 100) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.maxMessages = maxMessages;
  }

  /**
   * 检查是否需要压缩
   */
  shouldCompress(messageCount: number): boolean {
    return messageCount > this.maxMessages * this.config.thresholdPercent;
  }

  /**
   * 压缩消息数组
   * @param messages 原始消息数组
   * @param summaryGenerator 生成总结的函数（通常是 LLM 调用）
   */
  async compress(
    messages: Array<{ role: string; content: string }>,
    summaryGenerator?: (text: string) => Promise<string>
  ): Promise<CompressionResult> {
    const threshold = Math.floor(this.maxMessages * this.config.thresholdPercent);
    
    if (messages.length <= threshold) {
      return {
        original: messages.length,
        compressed: messages.length,
        summary: "",
        preserved: [...messages],
        removed: []
      };
    }

    const { protectFirst, protectLast } = this.config;
    const preserved: Array<{ role: string; content: string }> = [];
    const middle: Array<{ role: string; content: string }> = [];
    const removed: Array<{ role: string; content: string }> = [];

    // 保留前 N 条
    for (let i = 0; i < protectFirst; i++) {
      preserved.push(messages[i]);
    }

    // 中间部分待压缩
    for (let i = protectFirst; i < messages.length - protectLast; i++) {
      middle.push(messages[i]);
    }

    // 保留后 N 条
    for (let i = messages.length - protectLast; i < messages.length; i++) {
      preserved.push(messages[i]);
    }

    // 生成总结
    let summary = "";
    if (middle.length > 0 && summaryGenerator) {
      try {
        summary = await summaryGenerator(middle.map(m => m.content).join("\n\n"));
      } catch (e) {
        // 降级：简单总结
        summary = this.simpleSummary(middle);
      }
    } else if (middle.length > 0) {
      summary = this.simpleSummary(middle);
    }

    // 构建总结条目
    const summaryEntry = {
      role: "system",
      content: this.config.summaryPrefix
        .replace("{count}", String(middle.length))
        + "\n\n" + summary
    };

    // 记录被移除的消息
    removed.push(...middle);

    return {
      original: messages.length,
      compressed: preserved.length + 1,
      summary,
      preserved: [...preserved, summaryEntry],
      removed
    };
  }

  /**
   * 简单总结（无 LLM 时降级使用）
   */
  private simpleSummary(messages: Array<{ role: string; content: string }>): string {
    const userMessages = messages.filter(m => m.role === "user");
    const assistantMessages = messages.filter(m => m.role === "assistant");
    
    return [
      `[摘要 - ${messages.length} 条消息]`,
      `- ${userMessages.length} 条用户消息`,
      `- ${assistantMessages.length} 条助手回复`,
      "",
      "主要内容:",
      ...userMessages.slice(0, 5).map((m, i) => `  ${i + 1}. ${m.content.slice(0, 100)}${m.content.length > 100 ? "..." : ""}`)
    ].join("\n");
  }

  /**
   * 计算压缩率
   */
  getCompressionRatio(original: number, compressed: number): number {
    if (original === 0) return 0;
    return Math.round((1 - compressed / original) * 100);
  }

  /**
   * 获取当前阈值
   */
  getThreshold(): number {
    return Math.floor(this.maxMessages * this.config.thresholdPercent);
  }

  /**
   * 更新配置
   */
  updateConfig(config: Partial<CompressionConfig>): void {
    this.config = { ...this.config, ...config };
  }
}

// 导出单例
export const compressor = new ContextCompressor();
