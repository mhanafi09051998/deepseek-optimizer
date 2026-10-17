import { Plugin } from "@opencode/plugin"

const LIMIT = 8000
const HEAD = 3000
const TAIL = 4500
const ERROR = /(traceback|exception|assertionerror|error:|failed|fatal|panic|exit code [1-9])/i

function clip(text: string): string {
  if (text.length <= LIMIT) return text

  if (ERROR.test(text.slice(-2000))) {
    return `[tail of ${text.length} chars kept: error output]\n${text.slice(-LIMIT)}`
  }

  const head = text.slice(0, HEAD)
  const tail = text.slice(-TAIL)
  return `${head}\n[... ${text.length - HEAD - TAIL} chars omitted, tail follows ...]\n${tail}`
}

export default Plugin.define({
  id: "dso.truncate",
  async setup(ctx) {
    await ctx.tool.hook("execute.after", (event: any) => {
      if (event.status !== "completed") return
      const result = event.result
      if (!result || typeof result !== "object") return

      if (typeof result.output === "string") result.output = clip(result.output)
      if (typeof result.content === "string") result.content = clip(result.content)
      if (Array.isArray(result.content)) {
        for (const part of result.content) {
          if (part && typeof part.text === "string") part.text = clip(part.text)
        }
      }
    })
  },
})
