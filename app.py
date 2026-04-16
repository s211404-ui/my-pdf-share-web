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

st.title("🔒 柏宇的個人化 PDF 空間")

# --- 關鍵：用戶身份辨識 ---
st.info("為了區分您的檔案，請在下方設定一個存取碼。")
user_id = st.text_input("輸入您的專屬存取碼（建議使用學號或自訂英數組合）", type="password")

if not user_id:
    st.warning("請先輸入存取碼以開啟您的私有資料庫。")
    st.stop() # 沒輸入代碼前，不顯示後續功能

# 根據 user_id 決定雲端路徑
user_path = f"user_data/{user_id}"

# --- 第一部分：上傳區 ---
st.subheader(f"📤 上傳檔案至：{user_id} 的空間")
uploaded_file = st.file_uploader("選擇 PDF", type=["pdf"])

if uploaded_file:
    if st.button("🚀 上傳到我的空間"):
        with st.spinner("安全傳輸中..."):
            try:
                cloudinary.uploader.upload(
                    uploaded_file, 
                    resource_type = "raw", 
                    folder = user_path,
                    public_id = f"{uuid.uuid4()}_{uploaded_file.name}"
                )
                st.success("上傳成功！")
                st.rerun() 
            except Exception as e:
                st.error(f"上傳失敗: {e}")

st.divider()

# --- 第二部分：個人檔案清單 ---
st.subheader("📂 我的私有檔案清單")

try:
    # 只抓取 prefix 等於該用戶路徑的檔案
    resources = cloudinary.api.resources(
        type = "upload", 
        resource_type = "raw", 
        prefix = f"{user_path}/"
    )
    
    file_list = resources.get("resources", [])
    
    if not file_list:
        st.write("您的空間目前空空如也。")
    else:
        for file in file_list:
            # 只顯示純檔名
            display_name = file['public_id'].split('/')[-1]
            file_url = file['secure_url']
            
            with st.expander(f"📄 {display_name}"):
                st.code(file_url)
                st.markdown(f"[🔗 開啟 PDF]({file_url})")
                
except Exception as e:
    st.error("暫時無法讀取。請確認存取碼是否正確或 Cloudinary 權限。")