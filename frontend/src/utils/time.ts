import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'

dayjs.extend(utc)
dayjs.extend(timezone)

const TZ = 'Asia/Shanghai'

/**
 * 统一格式化后端时间。
 * - 若字符串不带时区（当前后端历史数据为 UTC 裸时间），按 UTC 解析
 * - 最终统一转换为 Asia/Shanghai 显示
 */
export function formatServerTime(value?: string | null): string {
  if (!value) return '-'

  const text = String(value).trim()
  if (!text) return '-'

  const hasOffset = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(text)
  const parsed = hasOffset ? dayjs(text) : dayjs.utc(text)

  if (!parsed.isValid()) return text
  return parsed.tz(TZ).format('YYYY-MM-DD HH:mm:ss')
}
