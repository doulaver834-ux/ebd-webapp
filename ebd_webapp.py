import streamlit as st
import datetime
import io

# === 导入核心模块 ===
import config
import ebd_core

# --- PDF Engine Imports ---
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch

# ==============================================================================
# 🎨 Vibe Coding: 高端医疗设备 UI 注入
# ==============================================================================
def inject_medical_ui_styles():
    st.markdown("""
        <style>
        /* 1. 引入工业级字体: IBM Plex Sans (兼具人文与机械感) */
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'IBM Plex Sans', sans-serif;
        }

        /* 2. 背景色：临床灰 (Clinical Gray) */
        .stApp {
            background-color: #F3F5F7;
        }

        /* 3. 侧边栏：控制台深灰 */
        section[data-testid="stSidebar"] {
            background-color: #FBFCFD;
            border-right: 1px solid #DDE1E6;
        }

        /* 4. 仪表盘卡片 (Metric Cards) - 模拟液晶显示屏 */
        div[data-testid="stMetric"] {
            background-color: #FFFFFF;
            border-left: 4px solid #0F62FE; /* IBM Blue / Surgical Blue */
            padding: 15px;
            border-radius: 4px; /* 微圆角，偏硬朗 */
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        div[data-testid="stMetric"] label {
            color: #525252; /* 弱化标签 */
            font-size: 0.85rem !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            color: #161616; /* 强化数值 */
            font-family: 'IBM Plex Mono', monospace; /* 数字等宽 */
            font-weight: 700;
        }

        /* 5. 按钮：物理按键质感 */
        div.stButton > button {
            background-color: #0F62FE;
            color: white;
            border: none;
            border-radius: 2px;
            font-weight: 600;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            transition: all 0.2s;
        }
        div.stButton > button:hover {
            background-color: #0353E9;
            box-shadow: 0 4px 8px rgba(15, 98, 254, 0.3);
            transform: translateY(-1px);
        }
        div.stButton > button:active {
            transform: translateY(1px);
        }

        /* 6. 警告与成功框：高对比度信号灯 */
        div.stAlert {
            border-radius: 2px;
            border: 1px solid rgba(0,0,0,0.1);
        }

        /* 标题修饰 */
        h1, h2, h3 {
            color: #161616;
            letter-spacing: -0.5px;
        }
        
        /* 进度条：精准刻度感 */
        .stProgress > div > div > div > div {
            background-color: #0F62FE;
        }
        </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 📄 PDF 生成逻辑 (保持不变，功能闭环)
# ==============================================================================
def generate_audit_report_pdf(context_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    
    elements = []
    elements.append(Paragraph("SCUT EBD CLINICAL AUDIT REPORT", styles['Heading1']))
    elements.append(Paragraph(f"ZONE: {context_data['zone_name']} | REF: {datetime.datetime.now().strftime('%Y%m%d-%H%M')}", styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))

    table_data = [['MODULE', 'METRICS', 'RESULT', 'DIAGNOSIS']]
    
    f = context_data['res_floor']
    table_data.append(["Surface Kinetics", f"DCOF: {context_data['inputs']['dcof']}", f['status'], Paragraph("<br/>".join(f['log']), styles['Normal'])])
    
    l = context_data['res_light']
    table_data.append(["Photobiological", f"Lux: {context_data['inputs']['lux']}", l['status'], Paragraph("<br/>".join(l['log']), styles['Normal'])])
    
    s = context_data['res_turn']
    table_data.append(["Spatial", f"Dia: {context_data['inputs']['turn']}mm", s['status'], Paragraph("<br/>".join(s['log']), styles['Normal'])])

    h = context_data['res_healing']
    table_data.append(["Psychosocial", f"Grade: {h['grade']}", f"{h['score']}", Paragraph("<br/>".join(h['log']), styles['Normal'])])

    t = Table(table_data, colWidths=[1.2*inch, 1.5*inch, 0.8*inch, 2.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#F3F5F7'),
        ('GRID', (0, 0), (-1, -1), 0.5, '#DDE1E6'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ]))
    
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ==============================================================================
# 🖥️ 主界面逻辑 (View Layer)
# ==============================================================================

st.set_page_config(page_title="EBD Audit Pro", page_icon="✚", layout="wide")

# 💉 注入 Vibe
inject_medical_ui_styles()

# 顶部 Header 模拟设备状态栏
c1, c2 = st.columns([4, 1])
with c1:
    st.title("EBD_SYSTEM_OS v3.1")
    st.caption("EVIDENCE-BASED DESIGN DIAGNOSTIC UNIT | SCUT ARCHITECTURE")
with c2:
    st.success("● SYSTEM ONLINE")

st.divider()

with st.sidebar:
    st.markdown("### ⚙️ CONTROL PANEL")
    
    zone_selection = st.selectbox("ZONE SELECTOR", list(config.ZONE_MAP.keys()))
    
    with st.expander("🛡️ PHYSICAL SAFETY", expanded=False):
        dcof_input = st.slider("DCOF (Friction)", 0.0, 1.0, 0.42)
        r_value_input = st.select_slider("DIN R-Value", options=[9, 10, 11, 12, 13], value=9)
        lux_input = st.number_input("Illuminance (Lux)", value=300)
        adj_lux_input = st.number_input("Adj. Lux", value=100)
        turning_dia = st.number_input("Turn Dia. (mm)", value=1500)
        slope_percent = st.number_input("Slope (%)", value=0.0)

    with st.expander("🧠 HEALING METRICS", expanded=True):
        material_count = st.slider("Material Count", 1, 10, 4)
        nature_ratio = st.slider("Green Ratio", 0.0, 1.0, 0.35)
        care_dist = st.number_input("Care Dist (m)", value=8.0)
        shade_coverage = st.slider("Shade Coverage", 0.0, 1.0, 0.5)

    st.markdown("---")
    run_audit = st.button("▶ INITIATE SCAN", type="primary")

if run_audit:
    # Call Core
    auditor_f = ebd_core.FloorSafetyAudit()
    res_floor = auditor_f.audit(zone_selection, slope_percent/100, dcof_input, r_value_input)
    
    auditor_l = ebd_core.LightingAudit()
    res_light = auditor_l.audit(zone_selection, lux_input, adj_lux_input)
    
    auditor_s = ebd_core.SpatialAudit()
    res_turn = auditor_s.audit_turning(turning_dia)
    
    auditor_h = ebd_core.HealingAudit()
    res_healing = auditor_h.calculate_score(material_count, nature_ratio, care_dist, shade_coverage)

    # View Layer
    t1, t2, t3, t4 = st.tabs(["🛡️ KINETICS", "💡 PHOTOBIO", "📐 SPATIAL", "🧠 PSYCHO"])
    
    with t1:
        c1, c2 = st.columns(2)
        c1.metric("STATUS", res_floor['status'])
        c2.metric("INPUT DCOF", dcof_input)
        for log in res_floor['log']: st.info(f"DIAGNOSIS: {log}")
    
    with t2:
        c1, c2 = st.columns(2)
        c1.metric("STATUS", res_light['status'])
        c2.metric("INPUT LUX", f"{lux_input} Lx")
        for log in res_light['log']: st.info(f"DIAGNOSIS: {log}")
        
    with t3:
        c1, c2 = st.columns(2)
        c1.metric("STATUS", res_turn['status'])
        c2.metric("DIA.", f"{turning_dia} mm")
        if res_turn['status'] == 'FAIL': st.error(res_turn['log'][0])

    with t4:
        c1, c2 = st.columns([1, 3])
        with c1:
            st.metric("HEALING SCORE", res_healing['score'], f"RANK: {res_healing['grade']}")
        with c2:
            st.progress(res_healing['score'] / 100)
            for log in res_healing['log']:
                if "✅" in log: st.success(log)
                elif "🚨" in log: st.error(log)
                else: st.warning(log)

    # PDF Generation
    pdf_context = {
        'zone_name': zone_selection,
        'inputs': {'dcof': dcof_input, 'lux': lux_input, 'turn': turning_dia},
        'res_floor': res_floor, 'res_light': res_light, 'res_turn': res_turn, 'res_healing': res_healing
    }
    
    pdf_file = generate_audit_report_pdf(pdf_context)
    st.download_button("📥 EXPORT CLINICAL REPORT", pdf_file, "EBD_Clinical_Report.pdf", "application/pdf")

else:
    # 待机状态画面
    st.info("AWAITING INPUT... SELECT PARAMETERS AND PRESS 'INITIATE SCAN'")