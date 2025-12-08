import time
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# ==============================================================================
# ⚙️ 系统配置：开启录制模式
# ==============================================================================
console = Console(record=True) 

# ==============================================================================
# 🛠️ 核心算法模块 (逻辑源自你的规范文档)
# ==============================================================================

class FloorSafetyAudit:
    """[模块 1] 地面材质安全审查"""
    def __init__(self):
        self.EBD_RAMP_BASE_DCOF = 0.60
        self.EBD_WET_RISK_UPLIFT = 0.55

    def audit(self, data):
        zone = data.get('zone_type')
        slope = data.get('slope', 0)
        dcof = data.get('dcof', 0)
        r_val = data.get('r_value', 0)
        
        req = {"dcof": 0.42, "r": 9, "ref": "ANSI A326.3"}
        notes = []
        status = "PASS"

        # 动态调整阈值 (循证逻辑)
        if slope > 0.02:
            req["dcof"] = self.EBD_RAMP_BASE_DCOF + (slope * 1.5)
            req["r"] = 11 if slope < 0.05 else 12
            req["ref"] = "EBD Physics + DIN 51130"
        elif zone == 'bathroom':
            req["dcof"] = self.EBD_WET_RISK_UPLIFT
            req["r"] = 11
            req["ref"] = "EBD Geriatric Safety Uplift"

        if dcof < req["dcof"]:
            status = "FAIL"
            notes.append(f"DCOF {dcof} < 阈值 {req['dcof']:.2f} ({req['ref']})")
        if r_val < req["r"]:
            status = "FAIL"
            notes.append(f"R-Value R{r_val} < 阈值 R{req['r']}")
        
        # 引用风险提示
        if status == "FAIL" and zone in ['bathroom', 'ramp_outdoor']:
            notes.append("[bold red]⚠ 警告: 基于 JAMA/Lancet 数据，此区域髋部骨折风险极高！[/bold red]")

        return {"status": status, "module": "地面防滑", "logs": notes}

class LightingAudit:
    """[模块 2] 光环境审查"""
    def __init__(self):
        self.MAX_RATIO = 3.0 # 明暗适应比限制

    def audit(self, data):
        lux = data.get('lux', 0)
        adj_lux = data.get('adjacent_lux', 0)
        target = 500 if data.get('zone_type') == 'bathroom' else 300
        notes = []
        status = "PASS"

        if lux < target:
            status = "FAIL"
            notes.append(f"照度 {lux}lx < 目标 {target}lx (IES RP-28-16)")
        
        # 防止瞬时致盲
        if adj_lux > 0:
            ratio = max(lux, adj_lux) / (min(lux, adj_lux) + 0.01)
            if ratio > self.MAX_RATIO:
                status = "FAIL"
                notes.append(f"明暗比 {ratio:.1f}:1 > {self.MAX_RATIO}:1 (易致瞬时盲区)")

        return {"status": status, "module": "光环境", "logs": notes}

class SpatialAudit:
    """[模块 4] 空间尺度审查"""
    def audit(self, data):
        dia = data.get('turning_diameter', 0)
        slope = data.get('slope', 0)
        notes = []
        status = "PASS"

        # ADA 1525mm 强条
        if dia > 0 and dia < 1525:
            status = "FAIL"
            notes.append(f"回转直径 {dia}mm < 1525mm (电动轮椅碰撞风险)")
        
        # 坡度体力消耗提示
        if slope > 1/20.0 and slope <= 1/12.0:
            status = "WARNING"
            notes.append("坡度符合 1:12 但体能消耗大，建议优化至 1:20")
        elif slope > 1/12.0:
            status = "FAIL"
            notes.append(f"坡度 {slope:.3f} > 1:12 (非法)")

        return {"status": status, "module": "空间尺度", "logs": notes}

# ==============================================================================
# 🧪 模拟数据
# ==============================================================================
def get_demo_cases():
    return [
        {
            "id": "ROOM-101 (不合格卫生间)",
            "params": {"zone_type": "bathroom", "dcof": 0.35, "r_value": 9, "lux": 150, "adjacent_lux": 600, "turning_diameter": 1400, "slope": 0}
        },
        {
            "id": "RAMP-202 (完美坡道)",
            "params": {"zone_type": "ramp_outdoor", "dcof": 0.70, "r_value": 12, "lux": 350, "adjacent_lux": 300, "turning_diameter": 1800, "slope": 0.05}
        }
    ]

# ==============================================================================
# 🎬 主程序：执行并生成报告
# ==============================================================================
def main():
    auditors = [FloorSafetyAudit(), LightingAudit(), SpatialAudit()]
    
    console.print(Panel.fit("[bold cyan]EBD-Auditor Pro (v2.0 Web版)[/bold cyan]\n[dim]正在生成数字化交付报告...[/dim]", border_style="cyan"))
    
    cases = get_demo_cases()
    
    for case in cases:
        console.print(f"\n[bold reverse] 正在审查: {case['id']} [/bold reverse]")
        table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta", width=100)
        table.add_column("审查模块", width=15)
        table.add_column("状态", justify="center", width=10)
        table.add_column("EBD 诊断日志 (基于实证医学数据)", style="dim")
        
        all_logs = []
        for auditor in auditors:
            result = auditor.audit(case['params'])
            icon = "[bold green]PASS[/bold green]" if result["status"] == "PASS" else ("[bold yellow]WARN[/bold yellow]" if result["status"] == "WARNING" else "[bold red]FAIL[/bold red]")
            log_text = result["logs"][0] if result["logs"] else "符合规范"
            table.add_row(result["module"], icon, log_text)
            if result["status"] != "PASS":
                for log in result["logs"]: all_logs.append(f"[{result['module']}] {log}")

        console.print(table)
        if all_logs:
            console.print(Panel("\n".join(all_logs), title="[red]整改建议书[/red]", border_style="red"))
        else:
            console.print(Panel("[green]设计卓越！符合全龄友好标准。[/green]", border_style="green"))
            
    # ==========================================================================
    # 💾 核心动作：保存 HTML
    # ==========================================================================
    output_filename = "EBD_Audit_Report.html"
    console.save_html(output_filename)
    
    # 获取文件的绝对路径，方便你找
    full_path = os.path.abspath(output_filename)
    print(f"\n\n✨ 报告已生成！")
    print(f"👉 请在浏览器打开此文件查看: {full_path}")

if __name__ == "__main__":
    main()