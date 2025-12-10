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
# 🧠 第一部分：核心算法逻辑
# ==============================================================================

class FloorSafetyAudit:
    """EBD-Audit-Spec v2.0 Module 1: Surface Kinetics Audit"""
    def __init__(self):
        self.ANSI_LEVEL_INTERIOR_WET = 0.42
        self.EBD_WET_RISK_UPLIFT = 0.55
        self.EBD_RAMP_BASE_DCOF = 0.60

    def audit_material(self, zone_type, slope_ratio, measured_dcof, din_r_value):
        requirements = {"min_dcof": 0.42, "min_r": 9, "standard_ref": "ANSI A326.3"}
        is_wet_zone = zone_type in ['卫生间 (Bathroom)', '餐厅 (Dining)', '康复水疗 (Therapy Pool)', '室外坡道 (Outdoor Ramp)']
        is_ramp = slope_ratio > 0.02

        if is_ramp:
            requirements["min_dcof"] = self.EBD_RAMP_BASE_DCOF + (slope_ratio * 1.5)
            requirements["min_r"] = 11 if slope_ratio < 0.05 else 12
            requirements["standard_ref"] = "EBD Physics + DIN 51130 (Ramp)"
        elif zone_type == '康复水疗 (Therapy Pool)':
            requirements["min_dcof"] = 0.60
            requirements["min_r"] = 12
            requirements["standard_ref"] = "ANSI Wet Plus / DIN 51097"
        elif is_wet_zone:
            requirements["min_dcof"] = self.EBD_WET_RISK_UPLIFT
            requirements["min_r"] = 11
            requirements["standard_ref"] = "EBD Geriatric Safety Uplift"

        notes = []
        status = "PASS"

        if measured_dcof < requirements["min_dcof"]:
            status = "FAIL"
            notes.append(f"DCOF {measured_dcof:.2f} < 阈值 {requirements['min_dcof']:.2f}")

        if din_r_value < requirements["min_r"]:
            status = "FAIL"
            notes.append(f"DIN R-Value R{din_r_value} < 阈值 R{requirements['min_r']}")

        if status == "FAIL" and zone_type in ['卫生间 (Bathroom)', '室外坡道 (Outdoor Ramp)']:
            notes.append("⚠ CRITICAL: 基于 JAMA/Lancet 风险模型，此区域髋部骨折概率极高。")

        return {"module": "地面安全", "status": status, "requirements": requirements, "log": notes}

class LightingAudit:
    """EBD-Audit-Spec v2.0 Module 2: Photobiological Audit"""
    def __init__(self):
        self.LUX_TARGETS = {
            '餐厅 (Dining)': 500, '阅读区 (Task)': 750, '普通走廊 (Corridor)': 300,
            '卫生间 (Bathroom)': 500, '康复水疗 (Therapy Pool)': 750, '室外坡道 (Outdoor Ramp)': 150
        }
        self.MAX_ADAPTATION_RATIO = 3.0

    def audit_space_lighting(self, zone_type, measured_lux, adjacent_zone_lux=None):
        target_lux = self.LUX_TARGETS.get(zone_type, 300)
        notes = []
        status = "PASS"

        if measured_lux < target_lux:
            status = "FAIL"
            notes.append(f"照度 {measured_lux} lx < 目标 {target_lux} lx (低照度增加跌倒风险 IRR 0.92)")

        if adjacent_zone_lux:
            ratio = max(measured_lux, adjacent_zone_lux) / (min(measured_lux, adjacent_zone_lux) + 0.01)
            if ratio > self.MAX_ADAPTATION_RATIO:
                status = "FAIL"
                notes.append(f"适应比 {ratio:.1f}:1 > {self.MAX_ADAPTATION_RATIO}:1 (瞬时盲区风险)")

        return {"module": "光环境", "status": status, "target_lux": target_lux, "log": notes}

class SpatialAudit:
    """EBD-Audit-Spec v2.0 Module 4: Spatial Kinematics Audit"""
    def __init__(self):
        self.MIN_TURNING_DIA = 1525.0
        self.MAX_SLOPE_HARD = 1 / 12.0
        self.MAX_SLOPE_SOFT = 1 / 20.0

    def audit_turning_circle(self, clear_width_mm):
        if clear_width_mm >= self.MIN_TURNING_DIA:
            return {"module": "空间回转", "status": "PASS", "log": []}
        else:
            return {"module": "空间回转", "status": "FAIL", "log": [f"回转直径 {clear_width_mm}mm < 1525mm (电动轮椅碰撞风险)"]}

    def audit_ramp_slope(self, slope_ratio):
        notes = []
        status = "PASS"
        if slope_ratio > self.MAX_SLOPE_HARD:
            status = "FAIL"
            notes.append(f"坡度 {slope_ratio:.3f} > 1:12 (非法且危险)")
        elif slope_ratio > self.MAX_SLOPE_SOFT:
            status = "WARNING"
            notes.append(f"坡度 {slope_ratio:.3f} 合法但非老年友好 (EBD建议 1:20)")
        return {"module": "空间坡度", "status": status, "log": notes}

# ==============================================================================
# 📄 第二部分：PDF 生成引擎
# ==============================================================================

def generate_audit_report_pdf(context_data):
    """生成 SCUT 风格的专业 PDF 报告"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('ReportTitle', parent=styles['Heading1'], alignment=1, fontSize=18, spaceAfter=20)
    subtitle_style = ParagraphStyle('ReportSub', parent=styles['Normal'], alignment=1, fontSize=10, textColor=colors.gray)
    
    elements = []
    
    # 1. Header
    elements.append(Paragraph("EBD Environmental Safety Audit Report", title_style))
    elements.append(Paragraph(f"Ref ID: SCUT-{datetime.datetime.now().strftime('%Y%m%d-%H%M')}", subtitle_style))
    elements.append(Paragraph(f"Zone: {context_data['zone_name']}", subtitle_style))
    elements.append(Spacer(1, 0.5 * inch))

    # 2. Data Table
    table_data = [['Audit Module', 'Measured Metric', 'Status', 'Notes']]
    
    # Row 1: Floor
    floor = context_data['res_floor']
    floor_notes = "\n".join(floor['log']) if floor['log'] else "Compliant"
    table_data.append([
        "Surface Kinetics", 
        f"DCOF: {context_data['inputs']['dcof']}\nR-Value: {context_data['inputs']['r_value']}", 
        floor['status'], 
        Paragraph(floor_notes, styles['Normal'])
    ])
    
    # Row 2: Light
    light = context_data['res_light']
    light_notes = "\n".join(light['log']) if light['log'] else "Compliant"
    table_data.append([
        "Photobiological", 
        f"Measured: {context_data['inputs']['lux']} lx\nTarget: {light.get('target_lux')} lx", 
        light['status'], 
        Paragraph(light_notes, styles['Normal'])
    ])
    
    # Row 3: Space
    space = context_data['res_turn']
    space_notes = "\n".join(space['log']) if space['log'] else "Compliant"
    table_data.append([
        "Spatial Kinematics", 
        f"Turn Dia: {context_data['inputs']['turn']}mm", 
        space['status'], 
        Paragraph(space_notes, styles['Normal'])
    ])

    # 3. Table Styling
    t = Table(table_data, colWidths=[1.2*inch, 1.5*inch, 0.8*inch, 2.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.dimgray),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    for i, row in enumerate(table_data[1:], start=1):
        status = row[2]
        if status == "FAIL":
            t.setStyle(TableStyle([('TEXTCOLOR', (2, i), (2, i), colors.red)]))
        elif status == "WARNING":
            t.setStyle(TableStyle([('TEXTCOLOR', (2, i), (2, i), colors.orange)]))
        else:
            t.setStyle(TableStyle([('TEXTCOLOR', (2, i), (2, i), colors.green)]))

    elements.append(t)
    elements.append(Spacer(1, 0.5 * inch))

    # 4. Certification Text
    elements.append(Paragraph("Certification Statement:", styles['Heading4']))
    elements.append(Paragraph(
        "This automated report is generated based on Evidence-Based Design (EBD) protocols derived from JAMA, The Lancet, and ADA standards.", 
        styles['Normal']
    ))
    
    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica-Oblique', 8)
        canvas.drawString(inch, 0.75 * inch, f"Generated by SCUT-AI Architecture Lab | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        canvas.restoreState()

    doc.build(elements, onFirstPage=add_footer)
    buffer.seek(0)
    return buffer

# ==============================================================================
# 🎨 第三部分：界面美化
# ==============================================================================

st.set_page_config(page_title="EBD 审查 Pro", page_icon="🏥", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #F8F9FA; color: #1F2937; }
    section[data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E5E7EB; }
    h1, h2, h3 { color: #111827 !important; font-family: 'Helvetica Neue', sans-serif; }
    div[data-testid="stMetric"], div[data-testid="stExpander"] {
        background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px; padding: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    div.stButton > button {
        background-color: #2563EB; color: white; border-radius: 6px; border: none; padding: 0.5rem 1rem; font-weight: 600;
    }
    div.stButton > button:hover { background-color: #1D4ED8; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🖥️ 第四部分：界面布局与交互
# ==============================================================================

col1, col2 = st.columns([1, 6])
with col1:
    st.markdown("## 🏥")
with col2:
    st.title("EBD 康复环境自动化审查系统")
    st.caption("SCUT Architecture | 基于 JAMA / The Lancet / ADA 实证数据驱动")

st.divider()

with st.sidebar:
    st.header("⚙️ 参数控制台")
    zone_map = {
        '普通走廊 (Corridor)': 'Corridor',
        '卫生间 (Bathroom)': 'Bathroom',
        '室外坡道 (Outdoor Ramp)': 'Outdoor Ramp',
        '康复水疗 (Therapy Pool)': 'Therapy Pool',
        '餐厅 (Dining)': 'Dining'
    }
    zone_selection = st.selectbox("空间类型", list(zone_map.keys()))
    zone_type = zone_selection
    zone_name_en = zone_map[zone_selection]
    
    with st.expander("🛡️ 地面参数", expanded=True):
        dcof_input = st.slider("DCOF 摩擦系数", 0.0, 1.0, 0.42, 0.01)
        r_value_input = st.select_slider("DIN 防滑等级", options=[9, 10, 11, 12, 13], value=9)
    
    with st.expander("💡 光环境参数"):
        lux_input = st.number_input("当前照度 (Lux)", value=300, step=10)
        adj_lux_input = st.number_input("相邻区域照度 (Lux)", value=100, step=10)
    
    with st.expander("📐 空间几何"):
        slope_percent = st.number_input("坡度百分比 (%)", value=0.0, step=0.1)
        slope_ratio = slope_percent / 100.0
        turning_dia = st.number_input("回转直径 (mm)", value=1500, step=50)
    
    st.markdown("---")
    run_audit = st.button("🚀 启动审查", type="primary")

if run_audit:
    floor_auditor = FloorSafetyAudit()
    light_auditor = LightingAudit()
    space_auditor = SpatialAudit()

    res_floor = floor_auditor.audit_material(zone_type, slope_ratio, dcof_input, r_value_input)
    res_light = light_auditor.audit_space_lighting(zone_type, lux_input, adj_lux_input)
    res_turn = space_auditor.audit_turning_circle(turning_dia)
    res_slope = space_auditor.audit_ramp_slope(slope_ratio)

    st.subheader(f"📊 审计报告：{zone_type}")
    
    tab1, tab2, tab3 = st.tabs(["🛡️ 地面安全", "💡 光环境", "📐 空间尺度"])
    
    with tab1:
        c1, c2 = st.columns(2)
        floor_state = "normal" if res_floor['status'] == 'PASS' else "inverse"
        c1.metric("实测 DCOF", f"{dcof_input}", delta="达标" if res_floor['status'] == 'PASS' else "-不达标", delta_color=floor_state)
        c2.metric("要求阈值", f"{res_floor['requirements']['min_dcof']:.2f}")
        if res_floor['status'] == 'PASS':
            st.success("✅ 地面材质符合 EBD 标准")
        else:
            st.error("🚨 **未通过**")
            for log in res_floor['log']: st.markdown(f"- {log}")
            st.info(f"参考: {res_floor['requirements']['standard_ref']}")

    with tab2:
        c1, c2 = st.columns(2)
        light_state = "normal" if res_light['status'] == 'PASS' else "inverse"
        c1.metric("实测照度", f"{lux_input} Lx", delta="舒适" if res_light['status'] == 'PASS' else "-风险", delta_color=light_state)
        c2.metric("目标照度", f"{res_light.get('target_lux')} Lx")
        if res_light['status'] == 'PASS':
            st.success("✅ 光环境适宜")
        else:
            st.error("🚨 **未通过**")
            for log in res_light['log']: st.markdown(f"- {log}")

    with tab3:
        if res_turn['status'] == 'FAIL':
            st.error(f"❌ {res_turn['log'][0]}")
        else:
            st.success(f"✅ 轮椅回转空间充足 ({turning_dia}mm)")
        if res_slope['status'] == 'FAIL':
            st.error(f"❌ {res_slope['log'][0]}")
        elif res_slope['status'] == 'WARNING':
            st.warning(f"⚠ {res_slope['log'][0]}")
        else:
            st.success("✅ 坡度设计极佳")

    st.markdown("---")
    pdf_context = {
        'zone_name': zone_name_en,
        'inputs': {'dcof': dcof_input, 'r_value': r_value_input, 'lux': lux_input, 'turn': turning_dia},
        'res_floor': res_floor,
        'res_light': res_light,
        'res_turn': res_turn
    }
    pdf_file = generate_audit_report_pdf(pdf_context)
    
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.success("📄 报告已生成完毕")
        st.download_button(
            label="📥 下载 PDF 正式审查报告 (SCUT Certified)",
            data=pdf_file,
            file_name=f"EBD_Audit_{datetime.datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

else:
    st.info("👈 请在左侧输入参数并点击“启动审查”")
    st.markdown("""
    <div style="text-align: center; color: #6B7280; padding: 40px;">
        <h3>系统就绪</h3>
        <p>支持国标 / ADA / JAMA 循证审查标准</p>
    </div>
    """, unsafe_allow_html=True)