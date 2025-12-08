import time
from typing import List, Dict, Any, Callable
from dataclasses import dataclass

# 引入 Rich 界面库
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

# ==========================================
# 1. 基础架构
# ==========================================

@dataclass
class SpaceElement:
    id: str
    category: str
    params: Dict[str, Any]

@dataclass
class AuditRule:
    id: str
    target_category: str
    description: str
    check_func: Callable[[Dict], tuple[bool, str, str]]

# ==========================================
# 2. 规则知识库 (已新增面积审查)
# ==========================================

def rule_toilet_door_width(params):
    """规则：无障碍卫生间门宽净尺寸不应小于 900mm"""
    width = params.get("door_width", 0)
    limit = 900
    if width >= limit:
        return True, f"{width}mm", "符合标准"
    else:
        return False, f"[red]{width}mm[/red]", f"需拓宽至 {limit}mm 以上"

def rule_toilet_emergency_call(params):
    """规则：必须设置紧急呼叫按钮"""
    has_call = params.get("has_emergency_call", False)
    if has_call:
        return True, "已设置", "符合标准"
    else:
        return False, "[red]未检测到[/red]", "必须在距地 400-500mm 处增设紧急呼叫按钮"

def rule_toilet_area(params):
    """【新增】规则：无障碍卫生间面积不小于 4.0 平方米"""
    area = params.get("area", 0)
    limit = 4.0
    if area >= limit:
        return True, f"{area}㎡", "空间充裕"
    else:
        return False, f"[red]{area}㎡[/red]", f"面积过小，建议扩大至 {limit}㎡ 以上"

def rule_ramp_slope(params):
    """规则：无障碍坡道坡度不应大于 1:12"""
    slope = params.get("slope_ratio", 0)
    limit = 1/12
    if slope <= limit + 0.001:
        ratio_str = f"1:{int(1/slope)}" if slope > 0 else "0"
        return True, ratio_str, "符合标准"
    else:
        ratio_str = f"1:{int(1/slope)}"
        return False, f"[red]{ratio_str}[/red]", "坡度过陡"

def rule_ramp_width(params):
    """规则：坡道净宽不应小于 1200mm"""
    width = params.get("width", 0)
    limit = 1200
    if width >= limit:
        return True, f"{width}mm", "符合标准"
    else:
        return False, f"[red]{width}mm[/red]", f"需拓宽至 {limit}mm 以上"

# 装载所有规则 (包括新加的 R-005)
ALL_RULES = [
    AuditRule("R-001", "Toilet", "门扇净宽审查", rule_toilet_door_width),
    AuditRule("R-002", "Toilet", "紧急呼叫装置", rule_toilet_emergency_call),
    AuditRule("R-005", "Toilet", "卫生间面积审查", rule_toilet_area), # <--- 新规则在这里！
    AuditRule("R-003", "Ramp", "坡道坡度审查", rule_ramp_slope),
    AuditRule("R-004", "Ramp", "坡道宽度审查", rule_ramp_width),
]

# ==========================================
# 3. 模拟数据 (恢复为待修复状态)
# ==========================================

def get_demo_data() -> List[SpaceElement]:
    return [
        # 案例 A: 卫生间 (这里我恢复成了不合格状态，为了让你看测试效果)
        SpaceElement(
            id="ROOM-101 (公卫)",
            category="Toilet",
            params={
                "door_width": 750,      # 不合格
                "has_emergency_call": False, # 不合格
                "area": 4.5             # 合格！(因为 > 4.0)
            }
        ),
        # 案例 B: 坡道
        SpaceElement(
            id="RAMP-002 (主入口)",
            category="Ramp",
            params={
                "slope_ratio": 0.08,
                "width": 1500,
                "material": "防滑地砖"
            }
        )
    ]

# ==========================================
# 4. 审计引擎
# ==========================================

def run_auditor():
    console.print(Panel.fit("[bold cyan]EBD-Auditor 自动化审查工具 v0.2[/bold cyan]", border_style="cyan"))
    console.print("[yellow]⚠ 正在加载新规则库 (v0.2)...[/yellow]")
    time.sleep(0.5)
    
    elements = get_demo_data()
    
    for element in elements:
        run_element_check(element)

def run_element_check(element: SpaceElement):
    table = Table(title=f"正在审查: {element.id} [{element.category}]", box=box.ROUNDED, expand=True)
    table.add_column("规则 ID", style="dim", width=8)
    table.add_column("审查项", style="cyan")
    table.add_column("实测值", justify="center")
    table.add_column("状态", justify="center")
    table.add_column("EBD 修正建议", style="italic")

    applicable_rules = [r for r in ALL_RULES if r.target_category == element.category]
    score = 0
    total = len(applicable_rules)

    for rule in applicable_rules:
        passed, measured_val, suggestion = rule.check_func(element.params)
        status_icon = "[bold green]PASS[/bold green]" if passed else "[bold red]FAIL[/bold red]"
        if passed: score += 1
        table.add_row(rule.id, rule.description, str(measured_val), status_icon, suggestion if not passed else "[dim]无[/dim]")

    console.print(table)
    console.print("")

if __name__ == "__main__":
    run_auditor()