import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

# --- 設定頁面資訊 ---
st.set_page_config(page_title="班級聚餐取餐系統", page_icon="🍱")

# --- 檔案設定 ---
MENU_FILE = "menu_config.json"
ORDER_FILE = "orders.csv"  # <--- 新增：這是我們的「共用簽到簿」

# --- 預設菜單 ---
DEFAULT_CONFIG = {
    "meals": {
        "A": "A餐 - 香煎雞腿飯",
        "B": "B餐 - 黑胡椒牛柳",
        "C": "C餐 - 奶油義大利麵 (素)",
        "D": "D餐 - 日式炸豬排"
    },
    "drinks": ["紅茶", "綠茶", "奶茶", "可樂", "雪碧", "檸檬水"]
}

# --- 函數：讀取與儲存菜單 ---
def load_config():
    if os.path.exists(MENU_FILE):
        try:
            with open(MENU_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG

def save_config(config):
    with open(MENU_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

# --- 函數：讀取與儲存訂單 (關鍵修改) ---
def load_orders():
    # 如果檔案存在，就讀取它；不存在就回傳空的 DataFrame
    if os.path.exists(ORDER_FILE):
        return pd.read_csv(ORDER_FILE)
    else:
        return pd.DataFrame(columns=["時間", "座號", "姓名", "主餐", "飲料", "冰塊", "備註", "領取狀態"])

def save_order(new_order_dict):
    # 讀取舊資料
    df = load_orders()
    # 建立新的一筆資料
    new_row = pd.DataFrame([new_order_dict])
    # 合併
    df = pd.concat([df, new_row], ignore_index=True)
    # 存檔 (index=False 代表不要存 0,1,2 這種行號)
    df.to_csv(ORDER_FILE, index=False, encoding="utf-8-sig")

# 初始化：載入菜單
menu_config = load_config()

# ================= 側邊欄：權限控制 =================
st.sidebar.header("🔐 身份驗證")
admin_password = st.sidebar.text_input("輸入管理員密碼", type="password")
ADMIN_KEY = "1234"

if admin_password == ADMIN_KEY:
    st.sidebar.success("管理員已登入")
    page = st.sidebar.radio("選擇功能", ["我要點餐", "📋 查看訂單 (後台)", "⚙️ 修改菜單 (設定)"])
else:
    page = "我要點餐"

# ================= 頁面 1: 點餐介面 =================
if page == "我要點餐":
    st.title("🍱 班級聚餐點餐系統")
    st.info("請輸入你的資料並選擇餐點")

    with st.form(key='order_form'):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("姓名", placeholder="例如：王小明")
        with col2:
            student_id = st.text_input("座號/學號", placeholder="例如：01")

        st.subheader("餐點選擇")
        meal_choice = st.selectbox("請選擇主餐", list(menu_config['meals'].values()))
        
        st.subheader("飲料客製化")
        c1, c2 = st.columns(2)
        with c1:
            drink_choice = st.selectbox("飲料種類", menu_config['drinks'])
        with c2:
            ice_choice = st.select_slider("冰塊調整", options=["正常冰", "少冰", "微冰", "去冰", "溫/熱"], value="少冰")

        note = st.text_area("備註 (過敏或特殊需求)", placeholder="無")

        submit_button = st.form_submit_button(label='送出訂單')

    if submit_button:
        if name and student_id:
            # 建立訂單資料
            new_order = {
                "時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "座號": student_id,
                "姓名": name,
                "主餐": meal_choice,
                "飲料": drink_choice,
                "冰塊": ice_choice,
                "備註": note,
                "領取狀態": "未領"
            }
            # 儲存到 CSV 檔案
            save_order(new_order)
            
            st.success(f"{name} 同學，你的訂單已送出！")
            st.balloons()
        else:
            st.error("請務必填寫姓名和座號！")

# ================= 頁面 2: 查看訂單 (讀取 CSV) =================
elif page == "📋 查看訂單 (後台)":
    st.title("📋 訂單總表")
    
    # 從 CSV 檔案讀取最新資料
    df = load_orders()
    
    if not df.empty:
        # 統計區
        st.write("### 📊 快速統計")
        col1, col2 = st.columns(2)
        col1.metric("總訂單數", len(df))
        if '主餐' in df.columns:
            col2.write(df['主餐'].value_counts())
        
        st.divider()

        # 搜尋功能
        search_term = st.text_input("🔍 搜尋姓名或座號", "")
        if search_term:
            # 確保欄位是字串型態再搜尋，避免報錯
            mask = df['姓名'].astype(str).str.contains(search_term) | df['座號'].astype(str).str.contains(search_term)
            filtered_df = df[mask]
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
            
        # 下載按鈕 (直接把目前的 CSV 讀出來給下載)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 下載訂單 CSV", csv, "class_orders.csv", "text/csv")
    else:
        st.warning("目前還沒有人點餐（CSV 檔案是空的）。")

# ================= 頁面 3: 修改菜單 =================
elif page == "⚙️ 修改菜單 (設定)":
    st.title("⚙️ 設定菜單選項")
    
    with st.form("menu_edit_form"):
        st.subheader("🍱 主餐選項 (JSON 格式)")
        current_meals_text = json.dumps(menu_config['meals'], ensure_ascii=False, indent=4)
        new_meals_str = st.text_area("編輯主餐", current_meals_text, height=200)
        
        st.subheader("🥤 飲料選項 (逗號分隔)")
        current_drinks_text = ", ".join(menu_config['drinks'])
        new_drinks_str = st.text_area("編輯飲料", current_drinks_text)
        
        save_btn = st.form_submit_button("💾 儲存設定")

    if save_btn:
        try:
            new_meals = json.loads(new_meals_str)
            new_drinks = [d.strip() for d in new_drinks_str.replace("，", ",").split(",")]
            new_config = {"meals": new_meals, "drinks": new_drinks}
            save_config(new_config)
            st.success("✅ 菜單已更新！請切換頁面查看。")
        except Exception as e:
            st.error(f"❌ 儲存失敗：{e}")