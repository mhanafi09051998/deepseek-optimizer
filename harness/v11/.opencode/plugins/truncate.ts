import { Plugin } from "@opencode/plugin"

const LIMIT = 4000

function clip(text: string): string {
  if (text.length <= LIMIT) return text
  const dropped = text.length - LIMIT
  return `${text.slice(0, LIMIT)}\n[truncated ${dropped} chars by dso]`
}

function clipResult(result: any): void {
  if (!result || typeof result !== "object") return

  if (typeof result.output === "string") {
    result.output = clip(result.output)
  }
  if (typeof result.content === "string") {
    result.content = clip(result.content)
  }
  if (Array.isArray(result.content)) {
    for (const part of result.content) {
      if (part && typeof part.text === "string") {
        part.text = clip(part.text)
      }
    }
  }
}

export default Plugin.define({
  id: "dso.truncate",
  async setup(ctx) {
    await ctx.tool.hook("execute.after", (event: any) => {
      if (event.status !== "completed") return
      clipResult(event.result)
    })
  },
})
