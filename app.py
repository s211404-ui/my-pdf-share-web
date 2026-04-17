import streamlit as st
import cloudinary
import cloudinary.uploader
import cloudinary.api
import uuid

# 1. 網頁基礎設定
st.set_page_config(page_title="柏宇的專屬 PDF 空間", page_icon="🔒")

# 2. 隱藏介面元素
st.markdown("<style>header {visibility: hidden;} #MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>", unsafe_allow_html=True)

# 3. Cloudinary 配置
cloudinary.config( 
  cloud_name = st.secrets["CLOUDINARY_NAME"], 
  api_key = st.secrets["CLOUDINARY_API_KEY"], 
  api_secret = st.secrets["CLOUDINARY_API_SECRET"],
  secure = True
)

# --- 標題與視覺引導區 ---
st.markdown("<h1 style='text-align: center;'>📄 柏宇的 PDF 雲端學習空間</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>快速轉換、永久儲存、AI摘要筆記</p>", unsafe_allow_html=True)

st.markdown("### 🚀 三步驟快速上手")
col1, col2, col3 = st.columns(3)

with col1:
    st.info("#### 1. 設定密碼\n輸入您的專屬存取碼，確保檔案隱私。")
    
with col2:
    st.info("#### 2. 上傳 PDF\n選取檔案並點擊上傳，系統自動雲端儲存。")
    
with col3:
    st.info("#### 3. AI 輔助\n點擊分析按鈕，獲取摘要與讀書筆記。")

st.divider()

# --- 關鍵：用戶身份辨識 (修正順序：先定義 user_id) ---
st.write("### 🔑 進入個人資料庫")
user_id = st.text_input("請輸入您的專屬存取碼（建議使用學號或自訂代碼）", type="password")

if not user_id:
    st.warning("請先輸入存取碼以開啟功能。")
    st.stop() # 沒輸入前，後面的內容都不會跑，避免錯誤

# 執行到這代表 user_id 已定義
st.success(f"✅ 已成功登入空間：{user_id}")

# 根據 user_id 決定雲端路徑
user_path = f"user_data/{user_id}"

# --- 第一部分：上傳區 ---
st.subheader(f"📤 上傳檔案")
uploaded_file = st.file_uploader("選擇 PDF 檔案", type=["pdf"])

if uploaded_file:
    if st.button("🚀 開始上傳"):
        with st.spinner("傳輸中..."):
            try:
                cloudinary.uploader.upload(
                    uploaded_file, 
                    resource_type = "raw", 
                    folder = user_path,
                    public_id = f"{uploaded_file.name}"
                )
                st.success("上傳成功！")
                st.rerun() 
            except Exception as e:
                st.error(f"上傳失敗: {e}")

st.divider()

# --- 第二部分：個人檔案清單 ---
st.subheader("📂 我上傳的私人檔案櫃")

try:
    resources = cloudinary.api.resources(
        type = "upload", 
        resource_type = "raw", 
        prefix = f"{user_path}/"
    )
    
    file_list = resources.get("resources", [])
    
    if not file_list:
        st.write("您的檔案櫃目前沒有檔案。")
    else:
        for file in file_list:
            display_name = file['public_id'].split('/')[-1]
            file_url = file['secure_url']
            
            with st.expander(f"📄 {display_name}"):
                st.code(file_url)
                st.markdown(f"[🔗 開啟 PDF]({file_url})")
                
except Exception as e:
    st.error("暫時無法讀取。請確認存取碼是否正確或 Cloudinary 權限。")