import streamlit as st
import cloudinary
import cloudinary.uploader
import cloudinary.api
import uuid

# 1. 網頁基礎設定 (分頁標題與圖示)
st.set_page_config(page_title="柏宇的 PDF 雲端庫", page_icon="📄")

# 2. 隱藏右上角所有選單、GitHub 圖標與底部浮水印 (增強專業感與安全性)
hide_st_style = """
            <style>
            header {visibility: hidden;}
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .stAppHeader {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# 3. 從 Streamlit 的「保險箱」讀取密鑰
cloudinary.config( 
  cloud_name = st.secrets["CLOUDINARY_NAME"], 
  api_key = st.secrets["CLOUDINARY_API_KEY"], 
  api_secret = st.secrets["CLOUDINARY_API_SECRET"],
  secure = True
)

st.title("📄 柏宇的 PDF 轉換與儲存器")
st.write("上傳 PDF 後，即可獲得永久分享連結，並可於下方查看所有紀錄。")

# --- 第一部分：上傳區 ---
st.subheader("📤 上傳新檔案")
uploaded_file = st.file_uploader("請選擇 PDF 檔案", type=["pdf"])

if uploaded_file is not None:
    if st.button("🚀 上傳並產生連結"):
        with st.spinner("上傳中..."):
            try:
                # 執行上傳
                # 將檔案存放在 pdfs/ 資料夾下，並結合 UUID 避免檔名重複
                upload_result = cloudinary.uploader.upload(
                    uploaded_file, 
                    resource_type = "raw", 
                    folder = "pdfs",
                    public_id = f"{uuid.uuid4()}_{uploaded_file.name}"
                )
                
                # 取得連結
                file_url = upload_result.get("secure_url")
                
                st.success("成功上傳！")
                st.code(file_url)
                st.markdown(f"[🔗 按此開啟 PDF]({file_url})")
                
                # 提示使用者並準備重新整理以更新下方清單
                st.info("網頁即將自動刷新，以更新下方檔案清單...")
                st.rerun() 
                
            except Exception as e:
                st.error(f"錯誤：{e}")

st.divider() # 畫一條橫線區隔

# --- 第二部分：雲端資料庫一覽 ---
st.subheader("📂 雲端檔案清單")

try:
    # 向 Cloudinary 請求 pdfs/ 資料夾下的所有檔案清單
    resources = cloudinary.api.resources(
        type = "upload", 
        resource_type = "raw", 
        prefix = "pdfs/"
    )
    
    file_list = resources.get("resources", [])
    
    if not file_list:
        st.info("目前資料庫中尚無檔案。")
    else:
        st.write(f"目前共儲存 {len(file_list)} 個檔案：")
        # 迴圈列出所有檔案
        for file in file_list:
            # 格式化顯示名稱 (去除 pdfs/ 前綴)
            display_name = file['public_id'].replace("pdfs/", "")
            file_url = file['secure_url']
            
            # 使用摺疊面板顯示，點開才顯示網址，畫面更整齊
            with st.expander(f"📄 {display_name}"):
                st.write("**檔案分享連結：**")
                st.code(file_url) # 方便使用者一鍵複製
                st.markdown(f"[🔗 開啟檔案]({file_url})")
                
except Exception as e:
    st.error("目前無法讀取清單。")
    st.info("💡 提示：請確認 Cloudinary 設定中的 'Resource list' 權限已開啟。")