import streamlit as st
import math

# ==============================================================================
# 🧠 第一部分：核心算法逻辑 (The Brain)
# ==============================================================================
# 基于你提供的 ebd_audit_core.py 复刻

class FloorSafetyAudit:
    """
    EBD-Audit-Spec v2.0 Module 1: Surface Kinetics Audit
    集成 ANSI A326.3, DIN 51130 和 GB 50763。
    """
    def __init__(self):
        self.ANSI_LEVEL_INTERIOR_WET = 0.42
        self.EBD_WET_RISK_UPLIFT = 0.55  # 老年高风险区修正
        self.EBD_RAMP_BASE_DCOF = 0.60   # 坡度物理补偿

    def audit_material(self, zone_type, slope_ratio, measured_dcof, din_r_value):
        requirements = {
            "min_dcof": 0.42,
            "min_r": 9,
            "standard_ref": "ANSI A326.3"
        }

        # 场景逻辑判断
        is_wet_zone = zone_type in ['卫生间 (Bathroom)', '餐厅 (Dining)', '康复水疗 (Therapy Pool)', '室外坡道 (Outdoor Ramp)']
        is_ramp = slope_ratio > 0.02

        # 严格等级应用 (Strictness Hierarchy)
        if is_ramp:
            requirements["min_dcof"] = self.EBD_RAMP_BASE_DCOF + (slope_ratio * 1.5)
            requirements["min_r"] = 11 if slope_ratio < 0.05 else 12
            requirements["standard_ref"] = "EBD Physics + DIN 51130 (Ramp)"
        elif zone_type == '康复水疗 (Therapy Pool)':
            requirements["min_dcof"] = 0.60
            requirements["min_r"] = 12
            requirements["standard_ref"] = "ANSI Interior Wet Plus / DIN 51097"
        elif is_wet_zone:
            requirements["min_dcof"] = self.EBD_WET_RISK_UPLIFT
            requirements["min_r"] = 11
            requirements["standard_ref"] = "EBD Geriatric Safety Uplift"

        # 执行审查
        notes = []
        status = "PASS"

        if measured_dcof < requirements["min_dcof"]:
            status = "FAIL"
            notes.append(f"DCOF {measured_dcof:.2f} < 阈值 {requirements['min_dcof']:.2f} ({requirements['standard_ref']})")

        if din_r_value < requirements["min_r"]:
            status = "FAIL"
            notes.append(f"DIN R-Value R{din_r_value} < 阈值 R{requirements['min_r']}")

        # 跌倒风险洞察
        if status == "FAIL" and zone_type in ['卫生间 (Bathroom)', '室外坡道 (Outdoor Ramp)']:
            notes.append("⚠ CRITICAL: 基于 JAMA/Lancet 风险模型，此区域髋部骨折概率极高。")

        return {"module": "地面安全", "status": status, "requirements": requirements, "log": notes}


class LightingAudit:
    """
    EBD-Audit-Spec v2.0 Module 2: Photobiological Audit
    来源: IES RP-28-16 (最严), WELL v2。
    """
    def __init__(self):
        self.LUX_TARGETS = {
            '餐厅 (Dining)': 500,
            '阅读区 (Task)': 750,
            '普通走廊 (Corridor)': 300,
            '卫生间 (Bathroom)': 500,
            '康复水疗 (Therapy Pool)': 750,
            '室外坡道 (Outdoor Ramp)': 150
        }
        self.MAX_ADAPTATION_RATIO = 3.0  # 明暗适应比

    def audit_space_lighting(self, zone_type, measured_lux, adjacent_zone_lux=None):
        target_lux = self.LUX_TARGETS.get(zone_type, 300)
        notes = []
        status = "PASS"

        # 绝对照度检查
        if measured_lux < target_lux:
            status = "FAIL"
            notes.append(f"照度 {measured_lux} lx < 目标 {target_lux} lx (低照度增加跌倒风险 IRR 0.92)")

        # 适应比检查
        if adjacent_zone_lux:
            ratio = max(measured_lux, adjacent_zone_lux) / (min(measured_lux, adjacent_zone_lux) + 0.01)
            if ratio > self.MAX_ADAPTATION_RATIO:
                status = "FAIL"
                notes.append(f"适应比 {ratio:.1f}:1 > {self.MAX_ADAPTATION_RATIO}:1 (进出存在瞬时盲区风险)")

        return {"module": "光环境", "status": status, "target_lux": target_lux, "log": notes}


class SpatialAudit:
    """
    EBD-Audit-Spec v2.0 Module 4: Spatial Kinematics Audit
    强制执行 ADA 2010 (1525mm) 标准。
    """
    def __init__(self):
        self.MIN_TURNING_DIA = 1525.0  # mm (ADA 60 inch)
        self.MAX_SLOPE_HARD = 1 / 12.0 # 8.33%
        self.MAX_SLOPE_SOFT = 1 / 20.0 # 5%

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
# 🎨 第二部分：UI 美化 (The Skin - SCUT Cyberpunk Theme)
# ==============================================================================

st.set_page_config(page_title="EBD Auditor Pro", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
    /* 1. 全局背景：深色科技风 */
    .stApp {
        background-color: #0E1117;
        background-image: radial-gradient(circle at 50% 0%, #1E293B 0%, #0E1117 70%);
        color: #E0E0E0;
    }

    /* 2. 侧边栏美化：磨砂玻璃 */
    section[data-testid="stSidebar"] {
        background-color: rgba(30, 41, 59, 0.5);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* 3. 标题渐变色 */
    h1 {
        background: linear-gradient(90deg, #4ADE80 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        padding-bottom: 10px;
    }

    /* 4. 卡片容器 (Metrics & Expanders) */
    div[data-testid="stMetric"], div[data-testid="stExpander"] {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: #4ADE80;
    }
    
    /* Metric 数值颜色修正 */
    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
    }

    /* 5. 按钮样式：绿色霓虹光效 */
    div.stButton > button {
        background: linear-gradient(90deg, #10B981 0%, #059669 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        padding: 0.6rem 2rem;
        width: 100%;
        transition: all 0.3s ease;
        text-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }
    div.stButton > button:hover {
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.6);
        transform: scale(1.02);
        color: white;
    }
    
    /* 6. 警告框美化 */
    .stAlert {
        background-color: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        color: #E0E0E0;
    }
    
    /* 7. Tabs 样式 */
    button[data-baseweb="tab"] {
        color: #94A3B8;
        font-weight: bold;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #4ADE80 !important;
        background-color: rgba(255,255,255,0.05) !important;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 🖥️ 第三部分：界面布局与交互 (The Interface)
# ==============================================================================

# 顶部 Logo 栏 (这里放一个占位 Logo，你可以换成 SCUT 校徽链接)
col_logo, col_title = st.columns([1, 6])
with col_logo:
    # 这是一个通用的建筑图标，你可以换成 https://www.scut.edu.cn/logo.png
    st.markdown("## 🏥") 
with col_title:
    st.title("EBD 康复环境自动化审查系统")
    st.caption("SCUT Architecture | 基于 JAMA / The Lancet / ADA 实证数据驱动")

st.divider()

# --- 侧边栏输入 ---
with st.sidebar:
    st.header("⚙️ 参数控制台")
    
    zone_type = st.selectbox(
        "空间类型 (Zone)", 
        ('普通走廊 (Corridor)', '卫生间 (Bathroom)', '室外坡道 (Outdoor Ramp)', '康复水疗 (Therapy Pool)', '餐厅 (Dining)')
    )
    
    with st.expander("🛡️ 地面参数 (Floor)", expanded=True):
        dcof_input = st.slider("DCOF 摩擦系数", 0.0, 1.0, 0.42, 0.01)
        r_value_input = st.select_slider("DIN 防滑等级", options=[9, 10, 11, 12, 13], value=9)
    
    with st.expander("💡 光环境参数 (Light)"):
        lux_input = st.number_input("当前照度 (Lux)", value=300, step=10)
        adj_lux_input = st.number_input("相邻区域照度 (Lux)", value=100, step=10, help="用于计算明暗适应比")
    
    with st.expander("📐 空间几何 (Spatial)"):
        slope_percent = st.number_input("坡度百分比 (%)", value=0.0, step=0.1, format="%.1f")
        slope_ratio = slope_percent / 100.0
        turning_dia = st.number_input("回转直径 (mm)", value=1500, step=50)
    
    st.markdown("---")
    run_audit = st.button("🚀 启动自动化审查 (Run Audit)")


# --- 主体内容区 ---
if run_audit:
    # 1. 实例化核心算法类
    floor_auditor = FloorSafetyAudit()
    light_auditor = LightingAudit()
    space_auditor = SpatialAudit()

    # 2. 运行计算
    res_floor = floor_auditor.audit_material(zone_type, slope_ratio, dcof_input, r_value_input)
    res_light = light_auditor.audit_space_lighting(zone_type, lux_input, adj_lux_input)
    res_turn = space_auditor.audit_turning_circle(turning_dia)
    res_slope = space_auditor.audit_ramp_slope(slope_ratio)

    # 3. 结果展示 (使用美化后的 Tabs)
    st.subheader(f"📊 审计报告：{zone_type}")
    
    tab1, tab2, tab3 = st.tabs(["🛡️ 地面安全", "💡 光环境", "📐 空间尺度"])
    
    # --- Tab 1: 地面 ---
    with tab1:
        c1, c2 = st.columns(2)
        
        # 状态判定颜色
        floor_state = "normal" if res_floor['status'] == 'PASS' else "inverse"
        floor_delta = "达标" if res_floor['status'] == 'PASS' else "-不达标 (FAIL)"
        
        c1.metric("实测 DCOF", f"{dcof_input}", delta=floor_delta, delta_color=floor_state)
        c2.metric("要求阈值", f"{res_floor['requirements']['min_dcof']:.2f}", help="基于坡度动态计算")
        
        if res_floor['status'] == 'PASS':
            st.success("✅ **通过**：地面材质符合 EBD 全龄友好标准。")
        else:
            # 错误日志展示
            st.error("🚨 **未通过 (FAIL)**")
            for log in res_floor['log']:
                st.markdown(f"- {log}")
            st.caption(f"参考依据: {res_floor['requirements']['standard_ref']}")

    # --- Tab 2: 光环境 ---
    with tab2:
        c1, c2 = st.columns(2)
        
        light_state = "normal" if res_light['status'] == 'PASS' else "inverse"
        light_delta = "舒适" if res_light['status'] == 'PASS' else "-风险 (FAIL)"
        
        c1.metric("实测照度", f"{lux_input} Lx", delta=light_delta, delta_color=light_state)
        c2.metric("目标照度", f"{res_light.get('target_lux')} Lx", help="IES RP-28-16 标准")
        
        if res_light['status'] == 'PASS':
            st.success("✅ **通过**：光环境设计适宜。")
        else:
            st.error("🚨 **未通过 (FAIL)**")
            for log in res_light['log']:
                st.markdown(f"- {log}")

    # --- Tab 3: 空间 ---
    with tab3:
        # 回转直径
        if res_turn['status'] == 'FAIL':
            st.error(f"❌ {res_turn['log'][0]}")
        else:
            st.success(f"✅ 轮椅回转空间充足 (当前: {turning_dia}mm)")
            
        st.divider()
        
        # 坡度
        if res_slope['status'] == 'FAIL':
            st.error(f"❌ {res_slope['log'][0]}")
        elif res_slope['status'] == 'WARNING':
            st.warning(f"⚠ {res_slope['log'][0]}")
        else:
            st.success("✅ 坡度设计极佳 (<= 1:20)")

else:
    # 初始状态：显示欢迎界面
    st.info("👈 请在左侧侧边栏配置参数，并点击“启动自动化审查”")
    
    # 占位符美化
    st.markdown("""
    <div style="text-align: center; padding: 60px; opacity: 0.6;">
        <h1 style="font-size: 60px;">🛡️</h1>
        <h3>System Ready</h3>
        <p>等待输入设计参数...</p>
    </div>
    """, unsafe_allow_html=True)