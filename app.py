import streamlit as st
import cloudinary
import cloudinary.uploader
import cloudinary.api
import uuid
import time
import google.generativeai as genai
from PyPDF2 import PdfReader
import io
import requests

# 1. 網頁基礎設定
st.set_page_config(page_title="柏宇的 AI PDF 空間", page_icon="🤖")

# 2. 隱藏介面元素
st.markdown("<style>header {visibility: hidden;} #MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>", unsafe_allow_html=True)

# 3. 配置區 (Cloudinary)
try:
    cloudinary.config( 
      cloud_name = st.secrets["CLOUDINARY_NAME"], 
      api_key = st.secrets["CLOUDINARY_API_KEY"], 
      api_secret = st.secrets["CLOUDINARY_API_SECRET"],
      secure = True
    )
except Exception as e:
    st.error(f"Cloudinary 設定失敗，請檢查 Secrets。錯誤: {e}")

# --- AI 初始化 (自動挑選可用模型) ---
ai_model = None  # 先初始化變數，避免出現 name not defined
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # 嘗試取得模型清單
    model_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    
    # 挑選模型順序：1.5-flash -> 任何 flash -> 第一個可用模型
    model_to_use = next((m for m in model_list if '1.5-flash' in m), 
                        next((m for m in model_list if 'flash' in m), model_list[0] if model_list else None))
    
    if model_to_use:
        ai_model = genai.GenerativeModel(model_to_use)
    else:
        st.error("找不到任何可用的 AI 模型。")
except Exception as e:
    st.error(f"AI 啟動失敗 (可能是 API 額度用盡)。錯誤訊息: {e}")

# --- 標題與流程說明 ---
st.markdown("<h1 style='text-align: center;'>📄 柏宇的 AI PDF 學習空間</h1>", unsafe_allow_html=True)
st.markdown("### 🚀 三步驟快速上手")
col1, col2, col3 = st.columns(3)
with col1: st.info("#### 1. 設定密碼\n你可以自訂自己的存取碼。")
with col2: st.info("#### 2. 上傳 PDF\n自動雲端儲存後將製成網站。")
with col3: st.info("#### 3. AI 筆記\nPDF可一鍵產生重點摘要。")
st.divider()

# --- 用戶身份辨識 ---
user_id = st.text_input("🔑 請輸入您的專屬存取碼", type="password")
if not user_id:
    st.warning("請先輸入存取碼以開啟功能。")
    st.stop()

user_path = f"user_data/{user_id}"

# --- 第一部分：上傳區 ---
st.subheader("📤 上傳新檔案")
uploaded_file = st.file_uploader("選擇 PDF 檔案", type=["pdf"])

if "last_upload_url" not in st.session_state:
    st.session_state.last_upload_url = None

if uploaded_file:
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > 10:
        st.error(f"❌ 檔案太大了！目前大小：{file_size_mb:.2f} MB")
        st.info("💡 Cloudinary 免費版限制單一檔案需小於 10 MB。")
    else:
        if st.button("🚀 開始上傳"):
            with st.spinner("檔案傳送中..."):
                try:
                    upload_result = cloudinary.uploader.upload(
                        uploaded_file, 
                        resource_type = "raw", 
                        folder = user_path,
                        public_id = uploaded_file.name
                    )
                    st.session_state.last_upload_url = upload_result['secure_url']
                    st.success("✅ 上傳成功！連結已生成。")
                except Exception as e:
                    st.error(f"上傳過程發生錯誤: {e}")

if st.session_state.last_upload_url:
    st.info("🔗 剛上傳的檔案連結：")
    st.code(st.session_state.last_upload_url)
    st.markdown(f"[點此在新分頁開啟檔案]({st.session_state.last_upload_url})")
    if st.button("🔄 更新下方檔案櫃清單"):
        st.rerun()

# --- 第二部分：個人檔案清單與 AI 功能 ---
st.subheader("📂 我的私有檔案清單")

def get_pdf_text(url):
    response = requests.get(url)
    f = io.BytesIO(response.content)
    reader = PdfReader(f)
    text = "".join([page.extract_text() for page in reader.pages])
    return text

try:
    resources = cloudinary.api.resources(type="upload", resource_type="raw", prefix=f"{user_path}/")
    all_files = resources.get("resources", [])
    
    if not all_files:
        st.write("目前尚無檔案。")
    else:
        show_all = st.toggle("顯示所有檔案 (取消 20 個的限制)", value=False)
        file_list = all_files if show_all else all_files[:20]
        
        st.caption(f"📊 狀態：總共 {len(all_files)} 個檔案，顯示最新 {len(file_list)} 個")
        st.divider()

        for file in file_list:
            display_name = file['public_id'].split('/')[-1]
            file_url = file['secure_url']
            
            with st.expander(f"📄 {display_name}"):
                st.write(f"網址：")
                st.code(file_url)
                
                # AI 分析
                if st.button(f"🤖 產生 AI 筆記", key=f"ai_{file['public_id']}"):
                    if ai_model is None:
                        st.error("AI 模型未啟動，請檢查 API 額度。")
                    else:
                        with st.spinner("AI 正在分析內容..."):
                            try:
                                pdf_text = get_pdf_text(file_url)
                                if len(pdf_text) < 10:
                                    st.error("讀不到文字！請確保 PDF 非純圖片。")
                                else:
                                    prompt = f"請分析以下內容並用繁體中文提供摘要與建議：\n\n{pdf_text[:8000]}"
                                    response = ai_model.generate_content(prompt)
                                    st.markdown("### 📝 AI 學習筆記")
                                    st.write(response.text)
                            except Exception as ai_err:
                                st.error(f"AI 分析失敗: {ai_err}")
                
                st.markdown(f"[🔗 直接開啟檔案]({file_url})")
                st.markdown("---")
                st.subheader("⚠️ 刪除區域")
                confirm_delete = st.checkbox(f"我確定要刪除", key=f"check_{file['public_id']}")
                if confirm_delete:
                    if st.button(f"🔥 確定永久刪除", key=f"btn_{file['public_id']}"):
                        result = cloudinary.uploader.destroy(file['public_id'], resource_type="raw")
                        if result.get("result") == "ok":
                            st.success("檔案已刪除！")
                            time.sleep(1)
                            st.rerun()

except Exception as e:
    st.error(f"讀取清單失敗：{e}")