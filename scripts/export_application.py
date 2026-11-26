"""导出深度诊断申请包（脱敏）。

设计依据（用户裁决）：
1. 申请包脱敏，只保留结构化字段——不进客户原话全文、不进企业真实名、不进联系方式
2. 第一周不做支付、不自动留资；「约」只触发付费意愿问句
3. 追问记录只带「经提炼的答案摘要」，不带原话
4. 证据等级随包传递，供深度诊断人工接手时判断可信度

输出：JSON 申请包 + 人读 Markdown摘要
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPTS_DIR.parent
CONTRACT = SKILL_DIR / "references" / "diagnosis_contract.json"

# 字段白名单：仅契约 field_bindings 中的字段可进包，其余一律丢弃
def _whitelist() -> set[str]:
    with open(CONTRACT, encoding="utf-8") as f:
        d = json.load(f)
    # 只取值为 dict 的项；note / questionnaire_default_only_rule 是说明项，不是字段
    return {k for k, v in d["field_bindings"].items() if isinstance(v, dict)}


# 脱敏：企业名换代号（取前2字+***），剔除手机号/邮箱/地址等
def _mask_company(name: str) -> str:
    """企业代号：不保留城市/地区，只按职能卡顺序给中性代号。"""
    name = (name or "").strip()
    if not name:
        return "企业A"
    # 去掉常见省市前缀，避免城市+行业+规模被反推定位
    for prefix in ("北京", "上海", "天津", "重庆", "江苏", "浙江", "广东", "山东", "河南", "河北", "四川", "湖北", "湖南", "安徽", "福建", "辽宁", "陕西", "山西", "江西", "广西", "云南", "贵州"):
        if name.startswith(prefix):
            name = name[len(prefix):].lstrip("省市")
            break
    return "企业A（已脱敏）"


def _scrub(text: str) -> str:
    """脱敏：去手机号/邮箱/身份证/详细地址。"""
    s = str(text or "")
    s = re.sub(r"1[3-9]\d{9}", "[手机号已脱敏]", s)
    s = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[邮箱已脱敏]", s)
    s = re.sub(r"\d{17}[\dXx]", "[证件号已脱敏]", s)
    s = re.sub(r"[\u4e00-\u9fa5]{2,}(路|大道|街|巷|区|镇|村)\S*", "[地址已脱敏]", s)
    s = re.sub(r"\d{3,}[号栋室层楼栋]", "[地址已脱敏]", s)
    return s


def _summary(answer: str, limit: int = 60) -> str:
    """经提炼的答案摘要，截断到 limit 字，不保留完整原话。"""
    s = re.sub(r"\s+", " ", str(answer or "")).strip()
    if len(s) > limit:
        return s[:limit] + "…"
    return s


def build_application(
    func_id: str,
    structured_fields: dict,
    answers: dict,
    grades: dict,
    company: str,
    hook_signals: dict | None = None,
) -> dict:
    """构建脱敏申请包字典。"""
    with open(CONTRACT, encoding="utf-8") as f:
        contract = json.load(f)

    func = next((x for x in contract["functions"] if x["id"] == func_id), None)
    if not func:
        return {"__error__": True, "message": f"未知职能卡 {func_id}"}

    wl = _whitelist()
    clean_fields = {k: v for k, v in (structured_fields or {}).items() if k in wl}

    # 追问摘要：段号 → {摘要, 证据等级}；只放摘要不放原话
    qa_summary = {}
    for seg, ans in (answers or {}).items():
        if ans:
            qa_summary[str(seg)] = {
                "摘要": _summary(_scrub(ans)),
                "证据等级": (grades or {}).get(str(seg), "C"),
            }

    return {
        "包类型": "深度诊断申请包",
        "契约版本": contract["meta"]["contract_version"],
        "导出时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "脱敏声明": "企业名已代号化；客户原话仅保留经提炼摘要；不含手机号/邮箱/地址/联系方式；第一周不做支付",
        "企业代号": _mask_company(company),
        "聚焦职能": {"id": func_id, "职能": func.get("function"), "档位": func.get("tier")},
        "六维判定状态": "未判定（免费版不出灯色；完整判定需15-20字段，在深度诊断阶段进行）",
        "结构化字段（白名单）": clean_fields,
        "访谈落点字段": [s.get("field") for s in func.get("segments", []) if s.get("field")],
        "追问摘要与证据等级": qa_summary,
        "接口/钩子信号": _scrub(json.dumps(hook_signals or {}, ensure_ascii=False)),
        "命中维度（待深度诊断确认）": func.get("hit_dimensions", []),
        "下一步": "人工接手：核对结构化字段 → 补充缺失字段至15-20项 → 完成六维判定与五环根因链 → 预约60分钟访谈",
    }


def export(pkg: dict, out_dir: Path) -> dict:
    """落盘 JSON + 人读 Markdown。"""
    if pkg.get("__error__"):
        return {"ok": False, "error": pkg["message"]}
    out_dir.mkdir(parents=True, exist_ok=True)
    ident = f"{pkg['企业代号'].replace('*','X')}_{pkg['聚焦职能']['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    jpath = out_dir / f"{ident}_申请包.json"
    jpath.write_text(json.dumps(pkg, ensure_ascii=False, indent=2), encoding="utf-8")

    # 人读摘要
    lines = [
        f"# 深度诊断申请包 · {pkg['企业代号']}",
        "",
        f"- 聚焦职能：{pkg['聚焦职能']['职能']}（{pkg['聚焦职能']['id']}档）",
        f"- 契约版本：{pkg['契约版本']}　导出时间：{pkg['导出时间']}",
        f"- 判定状态：{pkg['六维判定状态']}",
        "",
        "## 结构化字段（白名单）",
    ]
    for k, v in pkg["结构化字段（白名单）"].items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## 追问摘要与证据等级"]
    for seg, item in pkg["追问摘要与证据等级"].items():
        lines.append(f"- 段{seg} [{item['证据等级']}]: {item['摘要']}")
    lines += [
        "",
        "## 接口/钩子信号",
        pkg["接口/钩子信号"] or "（无）",
        "",
        "## 下一步",
        pkg["下一步"],
        "",
        "---",
        pkg["脱敏声明"],
    ]
    mpath = out_dir / f"{ident}_申请包摘要.md"
    mpath.write_text("\n".join(lines), encoding="utf-8")

    return {"ok": True, "json": str(jpath), "markdown": str(mpath)}


if __name__ == "__main__":
    print(json.dumps({"whitelist_fields": sorted(_whitelist())}, ensure_ascii=False, indent=2))
