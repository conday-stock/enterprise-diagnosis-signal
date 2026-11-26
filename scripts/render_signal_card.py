"""渲染免费版「深挖盲区卡」（两区：叙事区 + 访谈区钩子）。

硬约束（2026-11-25 产品口径变更后）：
1. 免费版不出灯色——本模块不 import 内核、不调用 run_pipeline()
2. 已验证：仅用追问字段出灯色会误判，故灯色留到深度诊断（付费）
3. 话术只来自 references/diagnosis_contract.json，本模块不内嵌话术
4. 零 LLM、零网络、零 key
5. 访谈区必须是三段式：需求认知 → 价值预告 → 操作指引
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

TEMPLATE = SKILL_DIR / "assets" / "signal_card_template.html"
CONTRACT = SKILL_DIR / "references" / "diagnosis_contract.json"


def _e(s) -> str:
    return html.escape(str(s if s is not None else ""))


def _load_contract() -> dict:
    with open(CONTRACT, encoding="utf-8") as f:
        return json.load(f)


def _find_function(contract: dict, func_id: str) -> dict:
    for f in contract["functions"]:
        if f["id"] == func_id:
            return f
    return {}


def _grade_label(grade: str) -> str:
    m = {"F": "事实", "I": "判断", "A": "感觉", "C": "待核实"}
    return m.get(grade, "未标注")


def _narr_block(func: dict, answers: dict, grades: dict) -> str:
    """叙事区：主假设 + 竞争解释 + 反证答案，附证据等级，无灯色。"""
    parts = []
    seg1 = next((s for s in func.get("segments", []) if s["stage"] == 1), None)
    a1 = answers.get("1", "")
    g1 = grades.get("1", "C")
    if seg1:
        if a1:
            parts.append(f"<p class='answer'><strong>你说的：</strong>{_e(a1)}<span class='egrade'>{_grade_label(g1)}</span></p>")
        parts.append(f"<p><strong>最值得注意的一点：</strong>{_e(func.get('exposure', ''))}</p>")
    seg2 = next((s for s in func.get("segments", []) if s["stage"] == 2), None)
    if seg2:
        a2 = answers.get("2", "")
        if a2:
            parts.append(f"<p class='answer'><strong>你补充的：</strong>{_e(a2)}</p>")
    seg3 = next((s for s in func.get("segments", []) if s["stage"] == 3), None)
    if seg3:
        a3 = answers.get("3", "")
        if a3:
            parts.append(f"<p class='answer'><strong>你举的情况：</strong>{_e(a3)}</p>")
    if g1 == "C":
        parts.append("<p class='timing'>你给的信息还不足以对上述判断做确认，这里只作为待核实线索列出。</p>")
    timing = func.get("timing_note")
    if timing:
        parts.append(f"<p class='timing'>时序提示：{_e(timing)}</p>")
    return "\n".join(parts)


def _hook_need(func: dict) -> str:
    hook = func.get("hook", "")
    return hook if hook else "这类问题真正的成因往往不在单一职能内部，而在几个环节的接口处——单点信息看不到那条链。"


def _hook_value(contract: dict) -> str:
    parts = contract.get("diagnosis_hook", {}).get("three_parts", [])
    return _e(parts[1]) if len(parts) > 1 else "深度诊断会用现象→证据→根因→影响→建议的五环链，把这个问题查到底。"


def _hook_action(contract: dict, func: dict) -> str:
    action = func.get("action", "")
    if action:
        return _e(action)
    parts = contract.get("diagnosis_hook", {}).get("three_parts", [])
    return _e(parts[2]) if len(parts) > 2 else "回复「约」，我发你深度诊断的入口。"


def _howto(contract: dict) -> str:
    return (
        "<ol>"
        "<li>回复「约」——这只是表达你想进一步了解，不产生任何费用。</li>"
        "<li>我会发你一个简短的深度诊断入口，你确认后再决定是否预约。</li>"
        "<li>深度诊断才会做完整的 15–20 项信息核对与六维判定，那时候才会给出灯色和根因链。</li>"
        "</ol>"
    )


def render(func_id: str, answers: dict, grades: dict, out_path: Path, company: str = "") -> dict:
    contract = _load_contract()
    func = _find_function(contract, func_id)
    if not func:
        return {"ok": False, "error": f"未知职能卡 {func_id}"}

    tpl = TEMPLATE.read_text(encoding="utf-8")
    rep = {
        "__TITLE__": (_e(company) + " · " if company else "") + "深挖盲区卡（免费版）",
        "__SUBTITLE__": f"聚焦职能：{_e(func.get('function', func_id))}",
        "__LEAD__": "这张卡不给灯色、不下诊断结论。它只做一件事：从你刚才的回答里，找出最值得深挖的那个盲区，并说明为什么它需要一次完整的诊断。",
        "__NARR_BLOCK__": _narr_block(func, answers, grades),
        "__HOOK_NEED__": _e(_hook_need(func)),
        "__HOOK_VALUE__": _hook_value(contract),
        "__HOOK_ACTION__": _hook_action(contract, func),
        "__HOWTO__": _howto(contract),
        "__DISCLAIMER__": "本卡为基于你所提供信息的初步信号，不构成诊断结论，也不包含灯色判定。"
                          + _e(contract["outreach"]["external_phrase"]),
    }
    for k, v in rep.items():
        tpl = tpl.replace(k, v)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(tpl, encoding="utf-8")
    return {"ok": True, "out": str(out_path), "function": func_id, "light": "none (免费版不出灯色)"}


if __name__ == "__main__":
    c = _load_contract()
    print(json.dumps({"contract_version": c["meta"]["contract_version"], "positioning": c["meta"].get("positioning_change_20261125")}, ensure_ascii=False, indent=2))
