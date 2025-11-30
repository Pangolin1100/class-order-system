import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

# --- 1. 頁面基礎設定 ---
st.set_page_config(page_title="班級聚餐取餐系統", page_icon="🍱", layout="wide")

# --- 2. 檔案路徑設定 ---
MENU_FILE = "menu_config.json"
ORDER_FILE = "orders.csv"

# --- 3. 預設菜單 (如果沒有設定檔時使用) ---
DEFAULT_CONFIG = {
    "meals": {
        "A": "A餐 - 香煎雞腿飯",
        "B": "B餐 - 黑胡椒牛柳",
        "C": "C餐 - 奶油義大利麵 (素)",
        "D": "D餐 - 日式炸豬排"
    },
    "drinks": ["紅茶", "綠茶", "奶茶", "可樂", "雪碧", "檸檬水"]
}

# --- 4. 工具函數 (讀寫檔案) ---

def load_config():
    """讀取菜單設定"""
    if os.path.exists(MENU_FILE):
        try:
            with open(MENU_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG

def save_config(config):
    """儲存菜單設定"""
    with open(MENU_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def load_orders():
    """讀取訂單 CSV，並處理領取狀態的格式"""
    if os.path.exists(ORDER_FILE):
        try:
            df = pd.read_csv(ORDER_FILE)
            
            # 確保「領取狀態」這一欄是布林值 (True/False)，這樣 Checkbox 才能運作
            if '領取狀態' in df.columns:
                # 把 "已領"/"未領" 這種文字轉成 True/False
                mask = df['領取狀態'].apply(lambda x: isinstance(x, str))
                if mask.any():
                    df.loc[mask, '領取狀態'] = df.loc[mask, '領取狀態'].replace({"已領": True, "未領": False, "True": True, "False": False})
                
                # 填補空值為 False，並強制轉型為布林
                df['領取狀態'] = df['領取狀態'].fillna(False).astype(bool)
            return df
        except Exception as e:
            st.error(f"讀取訂單發生錯誤: {e}")
            return pd.DataFrame(columns=["時間", "座號", "姓名", "主餐", "飲料", "冰塊", "備註", "領取狀態"])
    else:
        # 如果檔案不存在，回傳空表格
        return pd.DataFrame(columns=["時間", "座號", "姓名", "主餐", "飲料", "冰塊", "備註", "領取狀態"])

def save_orders_to_csv(df):
    """將訂單存回 CSV"""
    df.to_csv(ORDER_FILE, index=False, encoding="utf-8-sig")

# --- 5. 程式初始化 ---
menu_config = load_config()

# ================= 側邊欄：權限控制 =================
st.sidebar.header("🔐 身份驗證")
admin_password = st.sidebar.text_input("輸入管理員密碼", type="password")
ADMIN_KEY = "1234"  # <--- 在這裡修改您的密碼

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

        note = st.text_area("備註 (過敏或特殊需求)", placeholder="無")

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
            
            # 讀取舊資料 -> 合併新資料 -> 存檔
            df_current = load_orders()
            df_new = pd.DataFrame([new_order])
            
            # 確保新資料的「領取狀態」也是布林值
            df_new['領取狀態'] = df_new['領取狀態'].astype(bool)
            
            df_final = pd.concat([df_current, df_new], ignore_index=True)
            save_orders_to_csv(df_final)
            
            st.success(f"{name} 同學，你的訂單已送出！")
            st.balloons()
        else:
            st.error("請務必填寫姓名和座號！")

# ================= 頁面 2: 訂單管理 (後台) =================
elif page == "📋 訂單管理 (後台)":
    st.title("📋 訂單管理系統")
    st.write("💡 **操作說明**：勾選「已領取?」會自動存檔；選取左側空格按 `Delete` 鍵可刪除訂單。")
    
    # 讀取最新資料
    df = load_orders()
    
    if not df.empty:
        # --- 統計區塊 ---
        st.write("### 📊 訂單統計")
        col1, col2, col3 = st.columns(3)
        col1.metric("總訂單數", len(df))
        
        with col2:
            st.write("**🍱 主餐統計**")
            st.dataframe(df['主餐'].value_counts(), use_container_width=True, height=150)
            
        with col3:
            st.write("**🥤 飲料統計**")
            st.dataframe(df['飲料'].value_counts(), use_container_width=True, height=150)
        
        st.divider()

        # --- 編輯區塊 (Magic Table) ---
        st.write("### 📝 詳細訂單 (可編輯)")
        
        edited_df = st.data_editor(
            df,
            num_rows="dynamic", # 允許增加/刪除行
            use_container_width=True,
            column_config={
                "領取狀態": st.column_config.CheckboxColumn(
                    "已領取?",
                    help="打勾代表已領取",
                    default=False,
                ),
                "時間": st.column_config.TextColumn("下單時間", disabled=True), # 鎖定時間不可改
                "座號": st.column_config.TextColumn("座號", width="small"),
                "冰塊": st.column_config.TextColumn("冰塊", width="small"),
            },
            hide_index=True, # 隱藏索引欄
        )

        # --- 自動存檔 ---
        # 比較編輯後的表格與原表格，如果有差異就存檔
        if not df.equals(edited_df):
            save_orders_to_csv(edited_df)
            st.toast("✅ 資料已更新並儲存！", icon="💾")
            # 這裡可以選擇是否要 rerun，通常不強制 rerun 使用者體驗較好
            
        # 下載按鈕
        csv = edited_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 下載 Excel/CSV", csv, "class_orders.csv", "text/csv")
        
    else:
        st.warning("目前還沒有任何訂單。")

# ================= 頁面 3: 修改菜單 (設定) =================
elif page == "⚙️ 修改菜單 (設定)":
    st.title("⚙️ 設定菜單")
    st.info("在此修改菜單，點餐頁面會立即更新。")
    
    with st.form("menu_edit"):
        # 1. 主餐設定
        st.subheader("🍱 主餐選項 (JSON 格式)")
        # 將目前的設定轉為文字顯示
        meals_str = json.dumps(menu_config['meals'], ensure_ascii=False, indent=4)
        new_meals = st.text_area("請編輯下方的 JSON", meals_str, height=200)
        
        # 2. 飲料設定
        st.subheader("🥤 飲料選項")
        # 將清單轉為逗號分隔字串
        drinks_str = ", ".join(menu_config['drinks'])
        new_drinks = st.text_area("請用逗號隔開飲料名稱", drinks_str)
        
        # 3. 送出按鈕
        submitted = st.form_submit_button("💾 儲存菜單")

    # 處理表單送出 (這裡修復了之前的括號錯誤)
    if submitted:
        try:
            # 解析 JSON
            meals_data = json.loads(new_meals)
            
            # 解析飲料字串 (去除前後空白)
            drinks_data = [d.strip() for d in new_drinks.split(",")]
            
            # 組合新的設定
            final_config = {
                "meals": meals_data,
                "drinks": drinks_data
            }
            
            # 存檔
            save_config(final_config)
            st.success("✅ 菜單已更新！請切換頁面查看。")
            
        except Exception as e:
            st.error(f"❌ 格式錯誤，儲存失敗：{e}")
            st.warning("請檢查主餐是否為正確的 JSON 格式 (例如括號 {} 和引號 \"\" 是否成對)")