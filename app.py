import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

# --- 設定頁面資訊 ---
st.set_page_config(page_title="班級聚餐取餐系統", page_icon="🍱", layout="wide")

# --- 檔案設定 ---
MENU_FILE = "menu_config.json"
ORDER_FILE = "orders.csv"

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

# --- 函數區 ---
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

def load_orders():
    if os.path.exists(ORDER_FILE):
        # 讀取 CSV
        df = pd.read_csv(ORDER_FILE)
        # 為了讓 checkbox 正常運作，確保「領取狀態」欄位是布林值 (True/False)
        # 如果舊資料是寫 "未領/已領"，這裡會自動修正
        if '領取狀態' in df.columns:
            # 將文字轉為 True/False (如果是文字的話)
            mask = df['領取狀態'].apply(lambda x: isinstance(x, str))
            df.loc[mask, '領取狀態'] = df.loc[mask, '領取狀態'].replace({"已領": True, "未領": False})
            # 填補空值為 False
            df['領取狀態'] = df['領取狀態'].fillna(False).astype(bool)
        return df
    else:
        return pd.DataFrame(columns=["時間", "座號", "姓名", "主餐", "飲料", "冰塊", "備註", "領取狀態"])

def save_orders_to_csv(df):
    df.to_csv(ORDER_FILE, index=False, encoding="utf-8-sig")

# 初始化
menu_config = load_config()

# ================= 側邊欄：權限控制 =================
st.sidebar.header("🔐 身份驗證")
admin_password = st.sidebar.text_input("輸入管理員密碼", type="password")
ADMIN_KEY = "1234" # <--- 密碼在這裡

if admin_password == ADMIN_KEY:
    st.sidebar.success("管理員模式")
    page = st.sidebar.radio("功能選單", ["我要點餐", "📋 訂單管理 (後台)", "⚙️ 修改菜單 (設定)"])
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

        note = st.text_area("備註", placeholder="無")
        submit_button = st.form_submit_button(label='送出訂單')

    if submit_button:
        if name and student_id:
            new_order = {
                "時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "座號": student_id,
                "姓名": name,
                "主餐": meal_choice,
                "飲料": drink_choice,
                "冰塊": ice_choice,
                "備註": note,
                "領取狀態": False # 預設為 False (未領)
            }
            # 讀取舊的 -> 加上新的 -> 存檔
            df_current = load_orders()
            df_new = pd.DataFrame([new_order])
            df_final = pd.concat([df_current, df_new], ignore_index=True)
            save_orders_to_csv(df_final)
            
            st.success(f"{name} 同學，你的訂單已送出！")
            st.balloons()
        else:
            st.error("請務必填寫姓名和座號！")

# ================= 頁面 2: 訂單管理 (後台) - 這是這次升級的重點！ =================
elif page == "📋 訂單管理 (後台)":
    st.title("📋 訂單管理系統")
    st.write("💡 提示：你可以直接在表格上修改資料，或選取左側方框按 Delete 鍵刪除訂單。")
    
    # 讀取資料
    df = load_orders()
    
    if not df.empty:
        # --- 1. 統計區 (新增飲料統計) ---
        st.write("### 📊 訂單統計")
        col1, col2, col3 = st.columns(3)
        col1.metric("總訂單數", len(df))
        
        with col2:
            st.write("**🍱 主餐統計**")
            st.dataframe(df['主餐'].value_counts(), height=150)
            
        with col3:
            st.write("**🥤 飲料統計** (新功能)")
            st.dataframe(df['飲料'].value_counts(), height=150)
        
        st.divider()

        # --- 2. 可編輯的表格 (Magic Table) ---
        st.write("### 📝 詳細訂單 (可編輯)")
        
        # 這裡使用了 st.data_editor 來取代原本的 dataframe
        edited_df = st.data_editor(
            df,
            num_rows="dynamic", # 允許增加或刪除行
            use_container_width=True,
            column_config={
                "領取狀態": st.column_config.CheckboxColumn(
                    "已領取?",
                    help="打勾代表已領取",
                    default=False,
                ),
                "時間": st.column_config.TextColumn("下單時間", disabled=True), # 鎖定時間不讓改
            },
            hide_index=True, # 隱藏最前面的 0,1,2 數字
        )

        # --- 3. 自動存檔機制 ---
        # 如果編輯後的表格跟原本的不一樣，代表有人改過了，立刻存檔
        if not df.equals(edited_df):
            save_orders_to_csv(edited_df)
            st.toast("✅ 資料已自動更新並存檔！", icon="💾") # 跳出一個小通知
            
        # 下載按鈕
        csv = edited_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 下載 Excel/CSV", csv, "class_orders.csv", "text/csv")
        
    else:
        st.warning("目前還沒有訂單。")

# ================= 頁面 3: 修改菜單 =================
elif page == "⚙️ 修改菜單 (設定)":
    st.title("⚙️ 設定菜單")
    with st.form("menu_edit"):
        meals_str = json.dumps(menu_config['meals'], ensure_ascii=False, indent=4)
        new_meals = st.text_area("主餐設定 (JSON)", meals_str, height=200)
        
        drinks_str = ", ".join(menu_config['drinks'])
        new_drinks = st.text_area("飲料設定 (用逗號隔開)", drinks_str)
        
        if st.form_submit_button("💾 儲存菜單"):
            try:
                save_config({"meals": json.