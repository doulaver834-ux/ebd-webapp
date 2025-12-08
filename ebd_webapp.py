import streamlit as st
import math

# ==============================================================================
# 🧠 第一部分：核心算法 (源自你上传的 ebd_audit_core.py)
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
            notes.append(f"❌ DCOF {measured_dcof:.2f} < 阈值 {requirements['min_dcof']:.2f} ({requirements['standard_ref']})")

        if din_r_value < requirements["min_r"]:
            status = "FAIL"
            notes.append(f"❌ DIN R-Value R{din_r_value} < 阈值 R{requirements['min_r']}")

        if status == "FAIL" and zone_type in ['卫生间 (Bathroom)', '室外坡道 (Outdoor Ramp)']:
            notes.append("⚠ CRITICAL: 基于 JAMA/Lancet 风险模型，髋部骨折概率极高。")

        return {"module": "地面安全", "status": status, "requirements": requirements, "log": notes}

class LightingAudit:
    """EBD-Audit-Spec v2.0 Module 2: Photobiological Audit"""
    def __init__(self):
        self.LUX_TARGETS = {
            '餐厅 (Dining)': 500, '阅读区 (Task)': 750, '普通走廊 (Corridor)': 300,
            '卫生间 (Bathroom)': 500, '康复水疗 (Therapy)': 750, '室外坡道 (Outdoor Ramp)': 150
        }
        self.MAX_ADAPTATION_RATIO = 3.0
        self.MIN_UNIFORMITY = 0.7

    def audit_space_lighting(self, zone_type, measured_lux, adjacent_zone_lux=None, uniformity=1.0):
        target_lux = self.LUX_TARGETS.get(zone_type, 300)
        notes = []
        status = "PASS"

        if measured_lux < target_lux:
            status = "FAIL"
            notes.append(f"❌ 照度 {measured_lux} lx < 目标 {target_lux} lx (低照度增加跌倒风险 IRR 0.92)")

        if adjacent_zone_lux:
            ratio = max(measured_lux, adjacent_zone_lux) / (min(measured_lux, adjacent_zone_lux) + 0.01)
            if ratio > self.MAX_ADAPTATION_RATIO:
                status = "FAIL"
                notes.append(f"❌ 适应比 {ratio:.1f}:1 > {self.MAX_ADAPTATION_RATIO}:1 (瞬时盲区风险)")

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
            return {"module": "空间回转", "status": "FAIL", "log": [f"❌ 直径 {clear_width_mm}mm < 1525mm (电动轮椅碰撞风险)"]}

    def audit_ramp_slope(self, slope_ratio):
        notes = []
        status = "PASS"
        if slope_ratio > self.MAX_SLOPE_HARD:
            status = "FAIL"
            notes.append(f"❌ 坡度 {slope_ratio:.3f} > 1:12 (非法且危险)")
        elif slope_ratio > self.MAX_SLOPE_SOFT:
            status = "WARNING"
            notes.append(f"⚠ 坡度 {slope_ratio:.3f} 合法但非老年友好 (EBD建议 1:20)")
        return {"module": "空间坡度", "status": status, "log": notes}

# ==============================================================================
# 🎨 第二部分：Streamlit 界面 (Web UI)
# ==============================================================================

st.set_page_config(page_title="EBD 审查 Pro", page_icon="🏥", layout="wide")

st.title("🏥 EBD 康复环境自动化审查工具 (v3.0)")
st.markdown("> **SCUT Architecture** | 基于 `JAMA` / `The Lancet` / `ADA` 实证数据")
st.divider()

# --- 侧边栏输入 ---
st.sidebar.header("🛠️ 参数输入")

zone_type = st.sidebar.selectbox("空间类型",
    ('普通走廊 (Corridor)', '卫生间 (Bathroom)', '室外坡道 (Outdoor Ramp)', '康复水疗 (Therapy Pool)', '餐厅 (Dining)'))

st.sidebar.subheader("1. 地面")
dcof_input = st.sidebar.slider("DCOF 摩擦系数", 0.0, 1.0, 0.42, 0.01)
r_value_input = st.sidebar.select_slider("DIN 防滑等级", options=[9, 10, 11, 12, 13], value=9)

st.sidebar.subheader("2. 光环境")
lux_input = st.sidebar.number_input("当前照度 (Lux)", value=300, step=10)
adj_lux_input = st.sidebar.number_input("相邻区域照度 (Lux)", value=100, step=10)

st.sidebar.subheader("3. 空间")
slope_percent = st.sidebar.number_input("坡度 (%)", value=0.0, step=0.1)
slope_ratio = slope_percent / 100.0
turning_dia = st.sidebar.number_input("回转直径 (mm)", value=1500, step=50)

run_audit = st.sidebar.button("🚀 开始审查", type="primary")

# --- 审查逻辑与展示 ---
if run_audit:
    # 实例化顾问
    floor_auditor = FloorSafetyAudit()
    light_auditor = LightingAudit()
    space_auditor = SpatialAudit()

    # 运行计算
    res_floor = floor_auditor.audit_material(zone_type, slope_ratio, dcof_input, r_value_input)
    res_light = light_auditor.audit_space_lighting(zone_type, lux_input, adj_lux_input)
    res_turn = space_auditor.audit_turning_circle(turning_dia)
    res_slope = space_auditor.audit_ramp_slope(slope_ratio)

    # 📊 结果展示：使用 Tabs 分栏美化
    st.subheader(f"📊 审查报告：{zone_type}")
    
    tab1, tab2, tab3 = st.tabs(["🛡️ 地面安全", "💡 光环境", "📐 空间尺度"])

    # Tab 1: 地面
    with tab1:
        col1, col2 = st.columns(2)
        col1.metric("实测 DCOF", dcof_input, delta="-不达标" if res_floor['status']=='FAIL' else "达标")
        col2.metric("要求阈值", f"{res_floor['requirements']['min_dcof']:.2f}", help="基于坡度动态计算")
        
        if res_floor['status'] == 'PASS':
            st.success("✅ 地面材质符合 EBD 标准")
        else:
            st.error("\n\n".join(res_floor['log']))
            st.caption(f"参考标准: {res_floor['requirements']['standard_ref']}")

    # Tab 2: 光环境
    with tab2:
        col1, col2 = st.columns(2)
        col1.metric("实测照度", f"{lux_input} Lx", delta="-过暗" if res_light['status']=='FAIL' else "舒适")
        col2.metric("目标照度", f"{res_light.get('target_lux')} Lx", help="IES RP-28-16")
        
        if res_light['status'] == 'PASS':
            st.success("✅ 光环境适宜")
        else:
            st.error("\n\n".join(res_light['log']))

    # Tab 3: 空间
    with tab3:
        # 回转
        if res_turn['status'] == 'FAIL':
            st.error(res_turn['log'][0])
        else:
            st.success("✅ 轮椅回转空间充足 (ADA 标准)")
            
        # 坡度
        if res_slope['status'] == 'FAIL':
            st.error(res_slope['log'][0])
        elif res_slope['status'] == 'WARNING':
            st.warning(res_slope['log'][0])
        else:
            st.success("✅ 坡度设计极佳")

else:
    st.info("👈 请在左侧调整参数并点击审查")