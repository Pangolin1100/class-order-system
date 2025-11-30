import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

# --- 設定頁面資訊 ---
st.set_page_config(page_title="班級聚餐取餐系統", page_icon="🍱")

# --- 檔案設定 (用來儲存菜單) ---
MENU_FILE = "menu_config.json"

# --- 預設菜單 (如果第一次執行，會用這個) ---
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
        with open(MENU_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_CONFIG

def save_config(config):
    with open(MENU_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

# 初始化：載入菜單 與 訂單資料
menu_config = load_config()

if 'orders' not in st.session_state:
    st.session_state.orders = []

# ================= 側邊欄：權限控制 =================
st.sidebar.header("🔐 身份驗證")
# 只有輸入正確密碼，才會顯示後台選項
admin_password = st.sidebar.text_input("輸入管理員密碼", type="password")
ADMIN_KEY = "1234"  # <--- 你可以在這裡修改你的密碼

if admin_password == ADMIN_KEY:
    st.sidebar.success("管理員已登入")
    page = st.sidebar.radio("選擇功能", ["我要點餐", "📋 查看訂單 (後台)", "⚙️ 修改菜單 (設定)"])
else:
    # 密碼錯誤或沒輸入時，強制只能選點餐
    page = "我要點餐" 

# ================= 頁面 1: 點餐介面 (所有人可見) =================
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
        # 使用讀取到的菜單
        meal_choice = st.selectbox("請選擇主餐", list(menu_config['meals'].values()))
        
        st.subheader("飲料客製化")
        c1, c2 = st.columns(2)
        with c1:
            # 使用讀取到的飲料選單
            drink_choice = st.selectbox("飲料種類", menu_config['drinks'])
        with c2:
            ice_choice = st.select_slider("冰塊調整", options=["正常冰", "少冰", "微冰", "去冰", "溫/熱"], value="少冰")

        note = st.text_area("備註 (過敏或特殊需求)", placeholder="無")

        submit_button = st.form_submit_button(label='送出訂單')

    if submit_button:
        if name and student_id:
            new_order = {
                "時間": datetime.now().strftime("%H:%M:%S"),
                "座號": student_id,
                "姓名": name,
                "主餐": meal_choice,
                "飲料": drink_choice,
                "冰塊": ice_choice,
                "備註": note,
                "領取狀態": False
            }
            st.session_state.orders.append(new_order)
            st.success(f"{name} 同學，你的訂單已送出！")
            st.balloons()
        else:
            st.error("請務必填寫姓名和座號！")

# ================= 頁面 2: 查看訂單 (需密碼) =================
elif page == "📋 查看訂單 (後台)":
    st.title("📋 訂單總表")
    st.write("這裡是只有輸入密碼才看得到的後台。")
    
    if len(st.session_state.orders) > 0:
        df = pd.DataFrame(st.session_state.orders)
        
        # 統計區
        st.write("### 📊 快速統計")
        col1, col2 = st.columns(2)
        col1.metric("總訂單數", len(df))
        col2.write(df['主餐'].value_counts())
        
        st.divider()

        # 核對與搜尋
        search_term = st.text_input("🔍 搜尋姓名或座號", "")
        if search_term:
            filtered_df = df[df['姓名'].str.contains(search_term) | df['座號'].str.contains(search_term)]
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
            
        # 下載功能
        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8-sig')
        csv = convert_df(df)
        st.download_button("📥 下載訂單 CSV", csv, "class_orders.csv", "text/csv")
    else:
        st.warning("目前還沒有人點餐。")

# ================= 頁面 3: 修改菜單 (需密碼) =================
elif page == "⚙️ 修改菜單 (設定)":
    st.title("⚙️ 設定菜單選項")
    st.info("在這裡修改後，點餐頁面的選項會直接更新，下次開啟程式也會記得！")

    with st.form("menu_edit_form"):
        st.subheader("🍱 主餐選項 (格式：代號: 餐點名稱)")
        # 將字典轉換成文字讓使用者編輯
        current_meals_text = json.dumps(menu_config['meals'], ensure_ascii=False, indent=4)
        new_meals_str = st.text_area("編輯主餐 (請保持 JSON 格式)", current_meals_text, height=200)
        
        st.subheader("🥤 飲料選項 (用逗號分隔)")
        # 將列表轉換成字串讓使用者編輯
        current_drinks_text = ", ".join(menu_config['drinks'])
        new_drinks_str = st.text_area("編輯飲料", current_drinks_text)
        
        save_btn = st.form_submit_button("💾 儲存設定")

    if save_btn:
        try:
            # 解析並儲存
            new_meals = json.loads(new_meals_str)
            # 處理飲料字串，將全形逗號轉半形，並去除空白
            new_drinks = [d.strip() for d in new_drinks_str.replace("，", ",").split(",")]
            
            # 更新設定
            new_config = {"meals": new_meals, "drinks": new_drinks}
            save_config(new_config)
            
            # 強制重新整理頁面以套用新設定
            st.success("✅ 菜單已更新！請重新整理網頁，或是切換回點餐頁面查看。")
        except Exception as e:
            st.error(f"❌ 格式錯誤，儲存失敗：{e}")
            st.warning("請確認主餐欄位是否符合 JSON 格式 (記得要有大括號 {} 和雙引號 \"\")")