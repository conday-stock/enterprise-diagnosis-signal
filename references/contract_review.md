# 契约人读对照表（供核验 diagnosis_contract.json）

- 版本：1.0.0 ｜ 日期：2026-11-25
- 用途：核验机器契约是否忠实于 `深挖追问卡_v0.4_综合裁决版_20261125.md`
- 单一事实源：`references/diagnosis_contract.json`；本表只是人读镜像，不得反向改契约

## 一、卡清单（13 项 = v0.4 的 4A+4B+4C+G）

| ID | 职能 | 档 | 命中维度 | 判定落点字段 |
|---|---|---|---|---|
| A1 | 质量 | A | cost_quality / quality_delivery / finance | quality_loss_ratio → quality_assessment_misaligned → quality_loss_dev_ratio |
| A2 | 人力 | A | talent / org | key_post_backup_level → tech_turnover → boss_time_items → tech_capability_insufficient |
| A3 | 财务 | A | cost_quality / quality_delivery / customer | top3_customer_ratio → annual_price_cut → budget_cash_flow_test_done |
| A4 | 技术 | A | talent / quality_delivery | tech_turnover → tech_capability_insufficient（段5 rd_ratio 不命中，仅背景） |
| B1 | 战略 | B | 无直接命中 | — |
| B2 | 生产 | B | finance（准时率） | delivery_rate（可选） |
| B3 | IT/数字化 | B | 无直接命中 | — |
| B4 | 市场 | B（原 A5 降档） | customer | top3_customer_ratio（可选） |
| C1–C4 | 采购/物流/设备/工艺 | C | 无 | — |
| G | 模糊兜底 | router | — | 只路由，不出卡 |

## 二、关键核验点（逐条对 v0.4）

| # | 核验项 | v0.4 规定 | 契约实现 | 一致 |
|---|---|---|---|---|
| 1 | A 档数量 | 4 张（A5 降 B4） | A1–A4，B4 带 `promoted_from: A5` | ✅ |
| 2 | 反证段话术 | 识别场景式（我见过两种…） | 4 张 A 卡段3 全部为识别场景式 | ✅ |
| 3 | 段5二选一 | 必须二选一 | A1/A2/A3 段5 `binary: true`；A4 段5 标 `no_hit` | ✅ |
| 4 | 证据等级跟踪 | 主假设须标 [F]/[I]/[A]/[C] | 段1 `track_evidence_grade: true`；R4 规定 [C] 不出灯 | ✅ |
| 5 | 三区分离 | 判定/叙事/访谈分区，后两区无灯色 | 每段标 `zone`；`zones` 节定义 | ✅ |
| 6 | 接口代理字段 | boss_time_items/firefighting_freq_per_week | A2 段4 用 `boss_time_items`，proxy_note 记另一个 | ✅ |
| 7 | A1 三包滞后 | 固定提示 | `timing_note` 字段 | ✅ |
| 8 | 申请包脱敏 | 只保留结构化字段 | `outreach.action_phrase_note` + 阶段5执行 | ✅ |
| 9 | 对外话术 | 新资历版 | `outreach.external_phrase`，禁止句单列 | ✅ |
| 10 | 「约」动作 | 付费意愿问句，非支付 | `outreach.action_phrase_note`，B/C 卡 `action` 字段 | ✅ |

## 三、字段真实性核验（grep b3_lineage.py）

v0.4 引用的 15 个落点字段全部存在于 `FIELD_Q`：

```
key_post_backup_level: Q3    tech_turnover: Q3     tech_capability_insufficient: Q3
top3_customer_ratio: Q4      quality_loss_ratio: Q6 quality_loss_dev_ratio: Q6
quality_assessment_misaligned: Q6 (L49)             annual_price_cut: Q7
firefighting_freq_per_week: Q7                      cash_flow_fragile: Q11
boss_time_items: Q12         gross_margin_low: Q2   budget_cash_flow_test_done: Q11
delivery_rate: Q6            rd_ratio: Q8
```

对外显示题号：质量类字段（`quality_loss_ratio`/`quality_loss_dev_ratio`/`quality_assessment_misaligned`）血缘记 Q6，由 `b4_render._Q_DISPLAY_OVERRIDE` 显示为 Q7——契约 `field_bindings` 已同时记录两个题号。

## 四、待你确认

1. B4 市场卡降档后只保留可选落点 `top3_customer_ratio`，契约设为"判定区可选"——是否接受它偶尔出灯色？还是严格不出灯色？
2. A4 段5 `rd_ratio` 不命中六维，契约标 `zone: 叙事区`、`no_hit: true`——确认吗？
3. B/C 卡 `action` 统一为「约」动作，但第一周不做支付——确认"约"只触发问句、不自动留资吗？
