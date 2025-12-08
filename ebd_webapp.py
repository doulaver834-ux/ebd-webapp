import streamlit as st

# ==============================================================================
# 🧠 核心算法逻辑 (直接复用你的 EBD 内核)
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

        if slope > 0.02:
            req["dcof"] = self.EBD_RAMP_BASE_DCOF + (slope * 1.5)
            req["r"] = 11 if slope < 0.05 else 12
            req["ref"] = "EBD Physics + DIN 51130 (坡道修正)"
        elif zone == '卫生间 (Bathroom)':
            req["dcof"] = self.EBD_WET_RISK_UPLIFT
            req["r"] = 11
            req["ref"] = "EBD Geriatric Safety Uplift (老龄修正)"

        if dcof < req["dcof"]:
            status = "FAIL"
            notes.append(f"❌ 摩擦系数 {dcof} < 阈值 {req['dcof']:.2f} ({req['ref']})")
        if r_val < req["r"]:
            status = "FAIL"
            notes.append(f"❌ 防滑等级 R{r_val} < 阈值 R{req['r']}")
        
        if status == "FAIL" and zone in ['卫生间 (Bathroom)', '室外坡道 (Outdoor Ramp)']:
            notes.append("⚠ 严重警告: 基于 JAMA/Lancet 数据，此区域跌倒骨折风险极高！")

        return {"status": status, "logs": notes}

class LightingAudit:
    """[模块 2] 光环境审查"""
    def __init__(self):
        self.MAX_RATIO = 3.0

    def audit(self, data):
        lux = data.get('lux', 0)
        adj_lux = data.get('adjacent_lux', 0)
        target = 500 if '卫生间' in data.get('zone_type', '') else 300
        notes = []
        status = "PASS"

        if lux < target:
            status = "FAIL"
            notes.append(f"❌ 照度 {lux}lx < 目标 {target}lx (IES RP-28-16)")
        
        if adj_lux > 0:
            ratio = max(lux, adj_lux) / (min(lux, adj_lux) + 0.01)
            if ratio > self.MAX_RATIO:
                status = "FAIL"
                notes.append(f"❌ 明暗比 {ratio:.1f}:1 > {self.MAX_RATIO}:1 (易致瞬时盲区)")

        return {"status": status, "logs": notes}

class SpatialAudit:
    """[模块 4] 空间尺度审查"""
    def audit(self, data):
        dia = data.get('turning_diameter', 0)
        slope = data.get('slope', 0)
        notes = []
        status = "PASS"

        if dia > 0 and dia < 1525:
            status = "FAIL"
            notes.append(f"❌ 回转直径 {dia}mm < 1525mm (ADA标准: 电动轮椅碰撞风险)")
        
        if slope > 0:
            if slope > 1/12.0:
                status = "FAIL"
                notes.append(f"❌ 坡度 {slope:.3f} > 1:12 (非法坡度)")
            elif slope > 1/20.0:
                status = "WARNING"
                notes.append("⚠ 坡度合规但体能消耗大，建议优化至 1:20 (EBD建议)")

        return {"status": status, "logs": notes}

# ==============================================================================
# 🎨 Streamlit 界面构建 (前端 UI)
# ==============================================================================

# 1. 页面配置
st.set_page_config(page_title="EBD 自动化审查 Pro", page_icon="🏥", layout="wide")

st.title("🏥 EBD 康复环境自动化审查工具 (Web版)")
st.markdown("""
> **基于循证设计 (EBD) 与实证医学数据** > 集成标准：`JAMA` / `The Lancet` / `ADA 2010` / `IES RP-28-16`  
> *无需安装，在线输入参数即可获得专业诊断报告。*
""")

st.divider()

# 2. 侧边栏：参数输入区
st.sidebar.header("🛠️ 设计参数输入")

# --- 输入控件 ---
zone_type = st.sidebar.selectbox(
    "空间类型 (Zone Type)",
    ("普通走廊 (Corridor)", "卫生间 (Bathroom)", "室外坡道 (Outdoor Ramp)", "康复水疗 (Therapy Pool)")
)

st.sidebar.subheader("1. 地面参数")
dcof_input = st.sidebar.slider("湿态摩擦系数 (DCOF)", 0.0, 1.0, 0.42, 0.01)
r_value_input = st.sidebar.select_slider("DIN 防滑等级 (R-Value)", options=[9, 10, 11, 12, 13], value=9)

st.sidebar.subheader("2. 光环境参数")
lux_input = st.sidebar.number_input("主要区域照度 (Lux)", value=300, step=10)
adj_lux_input = st.sidebar.number_input("相邻区域照度 (Lux)", value=100, step=10, help="用于计算明暗适应比")

st.sidebar.subheader("3. 空间尺度")
slope_percent = st.sidebar.number_input("坡度百分比 (%)", value=0.0, step=0.1, format="%.1f")
slope_ratio = slope_percent / 100.0 # 转换为小数
turning_dia = st.sidebar.number_input("轮椅回转直径 (mm)", value=1500, step=50)

# 3. 触发按钮
run_audit = st.sidebar.button("🚀 开始审查 (Run Audit)", type="primary")

# ==============================================================================
# 🚀 执行审查与结果展示
# ==============================================================================

if run_audit:
    # 构造数据包
    data_packet = {
        "zone_type": zone_type,
        "dcof": dcof_input,
        "r_value": r_value_input,
        "lux": lux_input,
        "adjacent_lux": adj_lux_input,
        "slope": slope_ratio,
        "turning_diameter": turning_dia
    }

    # 实例化引擎
    auditors = [FloorSafetyAudit(), LightingAudit(), SpatialAudit()]
    
    st.subheader(f"📊 审查报告：{zone_type}")
    
    # 分栏显示结果
    col1, col2, col3 = st.columns(3)
    
    results = []
    for auditor in auditors:
        results.append(auditor.audit(data_packet))

    # 渲染结果卡片
    cols = [col1, col2, col3]
    module_names = ["地面防滑", "光环境", "空间尺度"]
    
    for i, res in enumerate(results):
        with cols[i]:
            if res["status"] == "PASS":
                st.success(f"**{module_names[i]}**\n\n✅ 通过")
            elif res["status"] == "WARNING":
                st.warning(f"**{module_names[i]}**\n\n⚠ 警告")
            else:
                st.error(f"**{module_names[i]}**\n\n❌ 违规")

    # 显示详细日志
    st.markdown("### 📝 详细诊断建议 (Evidence-Based Diagnosis)")
    
    has_error = False
    for res in results:
        if res["logs"]:
            for log in res["logs"]:
                if "警告" in log or "❌" in log:
                    st.error(log)
                    has_error = True
                elif "⚠" in log:
                    st.warning(log)
                    has_error = True
    
    if not has_error:
        st.balloons() # 只有全绿时才放气球！
        st.success("🎉 完美设计！该区域各项指标均符合 EBD 全龄友好标准。")
        
else:
    st.info("👈 请在左侧侧边栏调整参数，点击“开始审查”按钮。")