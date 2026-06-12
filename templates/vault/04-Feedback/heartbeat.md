---
last_scan: null
scan_status: "pending"
sessions_processed: 0
processed_sessions: {}
errors: []
script_version: "1.0.0"
---

# 扫描心跳 / Scanner Heartbeat

> 记录扫描器的运行状态。每次扫描自动更新。
> Records scanner runtime status. Auto-updated on each scan.

---

## 当前状态 / Current Status

- **最后扫描 / Last scan**: 尚未运行 / Not yet run
- **扫描状态 / Scan status**: `pending`
- **扫描器版本 / Script version**: 1.0.0

---

## 扫描统计 / Scan Stats

| 指标 / Metric | 值 / Value |
|---|---|
| 总处理 session 数 / Total sessions processed | 0 |
| 成功处理 / Successfully processed | 0 |
| 跳过的 / Skipped | 0 |
| 扫描错误 / Scan errors | 0 |

---

## 已处理的 Session / Processed Sessions

<!-- 格式 / Format:
| Session ID | 日期 / Date | 处理时间 / Processed At | 状态 / Status |
|---|---|---|---|
-->

暂无记录 / No records yet.

---

## 扫描错误 / Scan Errors

<!-- 格式 / Format:
| 时间 / Time | Session ID | 错误类型 / Error Type | 错误信息 / Error Message |
|---|---|---|---|
-->

暂无错误 / No errors yet.

---

## 说明 / Notes

- `scan_status` 值 / values:
  - `pending` — 从未运行 / Never run
  - `running` — 正在运行 / Currently running
  - `ok` — 上次运行正常 / Last run succeeded
  - `partial` — 部分成功（某些 session 处理失败）/ Partial success (some sessions failed)
  - `error` — 上次运行失败 / Last run failed
- `processed_sessions` 记录的是已处理的 session ID 集合，用于增量扫描
- `processed_sessions` is a set of processed session IDs, used for incremental scanning
