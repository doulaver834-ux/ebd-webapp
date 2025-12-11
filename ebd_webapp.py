import streamlit as st
import math
import datetime
import io

# --- PDF Engine Imports ---
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch

# ==============================================================================
# 🧠 第一部分：核心算法逻辑 (Modules 1-3 + Healing)
# ==============================================================================

class FloorSafetyAudit:
    """Module 1: Surface Kinetics Audit"""
    def __init__(self):
        self.EBD_RAMP_BASE_DCOF = 0.60

    def audit_material(self, zone_type, slope_ratio, measured_dcof, din_r_value):
        requirements = {"min_dcof": 0.42, "min_r": 9, "standard_ref": "ANSI A326.3"}
        is_wet_zone = zone_type in ['卫生间 (Bathroom)', '餐厅 (Dining)', '康复水疗 (Therapy Pool)', '室外坡道 (Outdoor Ramp)']
        
        if slope_ratio > 0.02:
            requirements["min_dcof"] = self.EBD_RAMP_BASE_DCOF + (slope_ratio * 1.5)
            requirements["min_r"] = 11 if slope_ratio < 0.05 else 12
            requirements["standard_ref"] = "EBD Physics + DIN 51130 (Ramp)"
        elif zone_type == '康复水疗 (Therapy Pool)':
            requirements["min_dcof"] = 0.60
            requirements["min_r"] = 12
        elif is_wet_zone:
            requirements["min_dcof"] = 0.55
            requirements["min_r"] = 11

        notes = []
        status = "PASS"

        if measured_dcof < requirements["min_dcof"]:
            status = "FAIL"
            notes.append(f"DCOF {measured_dcof:.2f} < 阈值 {requirements['min_dcof']:.2f}")

        if din_r_value < requirements["min_r"]:
            status = "FAIL"
            notes.append(f"DIN R-Value R{din_r_value} < 阈值 R{requirements['min_r']}")

        return {"module": "地面安全", "status": status, "requirements": requirements, "log": notes}

class LightingAudit:
    """Module 2: Photobiological Audit"""
    def __init__(self):
        self.LUX_TARGETS = {
            '餐厅 (Dining)': 500, '阅读区 (Task)': 750, '普通走廊 (Corridor)': 300,
            '卫生间 (Bathroom)': 500, '康复水疗 (Therapy Pool)': 750, '室外坡道 (Outdoor Ramp)': 150
        }

    def audit_space_lighting(self, zone_type, measured_lux, adjacent_zone_lux=None):
        target_lux = self.LUX_TARGETS.get(zone_type, 300)
        notes = []
        status = "PASS"

        if measured_lux < target_lux:
            status = "FAIL"
            notes.append(f"照度 {measured_lux} lx < 目标 {target_lux} lx")

        if adjacent_zone_lux:
            ratio = max(measured_lux, adjacent_zone_lux) / (min(measured_lux, adjacent_zone_lux) + 0.01)
            if ratio > 3.0:
                status = "FAIL"
                notes.append(f"适应比 {ratio:.1f}:1 > 3.0:1 (瞬时盲区风险)")

        return {"module": "光环境", "status": status, "target_lux": target_lux, "log": notes}

class SpatialAudit:
    """Module 4: Spatial Kinematics Audit"""
    def audit_turning_circle(self, clear_width_mm):
        if clear_width_mm >= 1525.0:
            return {"module": "空间回转", "status": "PASS", "log": []}
        return {"module": "空间回转", "status": "FAIL", "log": [f"回转直径 {clear_width_mm}mm < 1525mm"]}

    def audit_ramp_slope(self, slope_ratio):
        if slope_ratio > 0.0833: # 1:12
            return {"module": "空间坡度", "status": "FAIL", "log": [f"坡度 {slope_ratio:.3f} > 1:12 (非法)"]}
        elif slope_ratio > 0.05: # 1:20
            return {"module": "空间坡度", "status": "WARNING", "log": [f"坡度 {slope_ratio:.3f} 建议优化至 1:20"]}
        return {"module": "空间坡度", "status": "PASS", "log": []}

# === 🔥 新增模块: 心灵疗愈 (Module 3 - Based on Sun Jingjing/SRT) ===
class HealingAudit:
    """EBD-Audit-Spec v2.0 Module 3: Psychosocial Healing Audit"""
    
    def calculate_healing_score(self, material_count, view_nature_ratio, dist_care_child, shade_coverage):
        """
        计算 SCUT-Healing Score (SHS) 疗愈指数
        """
        notes = []
        
        # 1. 感官丰富度 (Sensory Entropy) - 倒U型曲线
        if 3 <= material_count <= 5:
            score_sensory = 100
            notes.append(f"✅ 材质丰富度适中 ({material_count}种)，符合 Berlyne 唤醒理论")
        elif material_count < 3:
            score_sensory = 60
            notes.append(f"⚠️ 材质过少 ({material_count}种)，存在感官剥夺风险")
        else:
            score_sensory = 70
            notes.append(f"⚠️ 材质过多 ({material_count}种)，可能导致认知过载")

        # 2. 自然疗愈力 (Biophilic Connection)
        # 线性插值：30% 及格，100% 满分
        score_nature = min((view_nature_ratio / 0.3) * 60 + 40, 100)
        if view_nature_ratio < 0.3:
            # 如果低于 30%，分数会很低
            notes.append(f"⚠️ 绿视率 {view_nature_ratio:.0%} < 30%，自然疗愈效能不足")
        else:
             notes.append(f"✅ 绿视率 {view_nature_ratio:.0%} 达标")

        # 3. 代际距离 (Intergenerational Distance) - 距离产生美
        if 6 <= dist_care_child <= 15:
            score_social = 100
            notes.append(f"✅ 看护距离 {dist_care_child}m 处于黄金区间 (Visible but not Audible)")
        else:
            score_social = 50
            notes.append(f"⚠️ 看护距离 {dist_care_child}m 不佳 (过近干扰/过远失控)")

        # --- 核心算法：加权总分 ---
        # 权重：感官(30%) + 自然(40%) + 社交(30%)
        base_score = 0.3 * score_sensory + 0.4 * score_nature + 0.3 * score_social
        
        # --- SCUT 地域性修正 (Shadow Utility) ---
        # 广州炎热气候特供逻辑
        final_score = base_score
        if shade_coverage < 0.4:
            final_score = base_score * 0.6 # 强制打6折
            notes.append(f"🚨 [SCUT地域修正] 阴影覆盖率 {shade_coverage:.0%} 过低！严重影响夏季使用，已惩罚。")

        # 评级系统
        grade = "S" if final_score >= 90 else ("A" if final_score >= 80 else "B")
        
        return {
            "module": "心灵疗愈",
            "score": round(final_score, 1), 
            "grade": grade,
            "log": notes
        }

# ==============================================================================
# 📄 第二部分：PDF 生成引擎 (已升级 - 含疗愈数据)
# ==============================================================================

def generate_audit_report_pdf(context_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    
    elements = []
    
    # 标题头
    elements.append(Paragraph("EBD Environmental Safety Audit Report", styles['Heading1']))
    elements.append(Paragraph(f"Zone: {context_data['zone_name']} | Ref: SCUT-{datetime.datetime.now().strftime('%H%M')}", styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))

    # 构建表格数据
    # Header
    table_data = [['Audit Module', 'Metrics', 'Status/Score', 'Notes']]
    
    # 1. Floor Data
    f = context_data['res_floor']
    table_data.append(["Surface Kinetics", f"DCOF: {context_data['inputs']['dcof']}", f['status'], Paragraph("\n".join(f['log']), styles['Normal'])])
    
    # 2. Light Data
    l = context_data['res_light']
    table_data.append(["Photobiological", f"Lux: {context_data['inputs']['lux']}", l['status'], Paragraph("\n".join(l['log']), styles['Normal'])])
    
    # 3. Space Data
    s = context_data['res_turn']
    table_data.append(["Spatial", f"Dia: {context_data['inputs']['turn']}mm", s['status'], Paragraph("\n".join(s['log']), styles['Normal'])])

    # 4. Healing Data (New!)
    h = context_data['res_healing']
    # 格式化 log 显示
    h_notes = "<br/>".join(h['log'])
    table_data.append([
        "Psychosocial Healing", 
        f"Grade: {h['grade']}", 
        f"Score: {h['score']}", 
        Paragraph(h_notes, styles['Normal'])
    ])

    # 表格样式
    t = Table(table_data, colWidths=[1.2*inch, 1.5*inch, 0.8*inch, 2.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ]))
    
    elements.append(t)
    
    # 认证落款
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph("Certification Statement:", styles['Heading4']))
    elements.append(Paragraph(
        "This report integrates physical safety audits (ANSI/ADA) with psychosocial healing metrics (SCUT-SRT).", 
        styles['Normal']
    ))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ==============================================================================
# 🖥️ 第三部分：界面布局 (已升级 - 含疗愈 Tab)
# ==============================================================================

st.set_page_config(page_title="EBD 审查 Pro v2.1", page_icon="🏥", layout="wide")

st.title("EBD 康复环境自动化审查系统 v2.1")
st.caption("SCUT Architecture | 集成物理安全与心理疗愈评估模型 (Based on Sun Jingjing Theory)")

with st.sidebar:
    st.header("⚙️ 参数控制台")
    
    # 基础参数
    zone_selection = st.selectbox("空间类型", ['普通走廊 (Corridor)', '卫生间 (Bathroom)', '室外坡道 (Outdoor Ramp)', '康复水疗 (Therapy Pool)', '餐厅 (Dining)'])
    
    with st.expander("🛡️ 物理安全参数", expanded=False):
        dcof_input = st.slider("DCOF 摩擦系数", 0.0, 1.0, 0.42)
        r_value_input = st.select_slider("DIN 防滑等级", options=[9, 10, 11, 12, 13], value=9)
        lux_input = st.number_input("当前照度 (Lux)", value=300)
        adj_lux_input = st.number_input("相邻区域照度 (Lux)", value=100)
        turning_dia = st.number_input("回转直径 (mm)", value=1500)
        slope_percent = st.number_input("坡度百分比 (%)", value=0.0)

    # === 🔥 新增输入: 疗愈感知参数 ===
    with st.expander("🧠 疗愈感知参数 (Psychosocial)", expanded=True):
        st.caption("基于孙晶晶/SRT 理论框架")
        material_count = st.slider("主要材质数量 (感官熵)", 1, 10, 4, help="建议值 3-5 种 (Berlyne)")
        nature_ratio = st.slider("自然景观占比 (绿视率)", 0.0, 1.0, 0.35, help="视野内绿色植物占比")
        care_dist = st.number_input("看护-游乐距离 (m)", value=8.0, help="代际互动距离，建议 6-15m")
        shade_coverage = st.slider("有效阴影覆盖率", 0.0, 1.0, 0.5, help="SCUT地域修正：针对广州炎热气候")

    run_audit = st.button("🚀 启动全面审查", type="primary")

if run_audit:
    # 实例化所有审计官
    floor_auditor = FloorSafetyAudit()
    light_auditor = LightingAudit()
    space_auditor = SpatialAudit()
    healing_auditor = HealingAudit() # New Instance

    # 执行计算
    res_floor = floor_auditor.audit_material(zone_selection, slope_percent/100, dcof_input, r_value_input)
    res_light = light_auditor.audit_space_lighting(zone_selection, lux_input, adj_lux_input)
    res_turn = space_auditor.audit_turning_circle(turning_dia)
    # 执行疗愈计算
    res_healing = healing_auditor.calculate_healing_score(material_count, nature_ratio, care_dist, shade_coverage)

    # 结果展示
    st.divider()
    t1, t2, t3, t4 = st.tabs(["🛡️ 地面安全", "💡 光环境", "📐 空间尺度", "🧠 心灵疗愈"])
    
    with t1:
        st.metric("状态", res_floor['status'], f"DCOF {dcof_input}")
        for l in res_floor['log']: st.info(l)

    with t2:
        st.metric("状态", res_light['status'], f"{lux_input} Lx")
        for l in res_light['log']: st.info(l)
        
    with t3:
        st.metric("回转", res_turn['status'], f"{turning_dia} mm")
        if res_turn['status'] == 'FAIL': st.error(res_turn['log'][0])
        else: st.success("符合无障碍通行标准")

    # === 🔥 新增展示: 疗愈结果 ===
    with t4:
        c1, c2 = st.columns([1, 3])
        with c1:
            # 动态颜色
            grade_color = "normal"
            if res_healing['grade'] == 'S': grade_color = "normal" # Streamlit metric doesn't allow custom colors easily, relying on delta
            
            st.metric("SCUT疗愈指数", f"{res_healing['score']} 分", f"评级: {res_healing['grade']}")
        
        with c2:
            st.caption("综合疗愈效能进度")
            st.progress(res_healing['score'] / 100)
            
            if res_healing['grade'] == 'S':
                st.success("🌟 S级空间！完美的疗愈环境，符合所有循证设计指标。")
            elif res_healing['grade'] == 'A':
                st.info("✨ A级空间 - 表现优秀，部分细节可微调。")
            else:
                st.warning("⚠️ B级空间 - 体验有待优化，请关注下方建议。")
            
            # 显示详细日志
            for log in res_healing['log']:
                if "✅" in log: st.success(log)
                elif "🚨" in log: st.error(log)
                else: st.warning(log)

    # PDF 生成上下文构建
    pdf_context = {
        'zone_name': zone_selection,
        'inputs': {'dcof': dcof_input, 'lux': lux_input, 'turn': turning_dia},
        'res_floor': res_floor, 
        'res_light': res_light, 
        'res_turn': res_turn, 
        'res_healing': res_healing # 将疗愈结果传入 PDF 引擎
    }
    
    pdf_file = generate_audit_report_pdf(pdf_context)
    
    st.download_button(
        label="📥 下载完整版 EBD 报告 (含疗愈分析)", 
        data=pdf_file, 
        file_name=f"SCUT_EBD_Report_{datetime.datetime.now().strftime('%Y%m%d')}.pdf", 
        mime="application/pdf", 
        use_container_width=True
    )