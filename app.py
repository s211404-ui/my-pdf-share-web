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
import cloudinary.uploader

# 1. 網頁基礎設定
st.set_page_config(page_title="柏宇的 AI PDF 空間", page_icon="🤖")

# 2. 隱藏介面元素
st.markdown("<style>header {visibility: hidden;} #MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>", unsafe_allow_html=True)

# 3. 配置區 (Cloudinary + Gemini)
cloudinary.config( 
  cloud_name = st.secrets["CLOUDINARY_NAME"], 
  api_key = st.secrets["CLOUDINARY_API_KEY"], 
  api_secret = st.secrets["CLOUDINARY_API_SECRET"],
  secure = True
)

# 初始化 Gemini AI
# --- 修正後的 AI 初始化 ---
# --- 修正後的 AI 初始化 (完全取代原本那兩三行) ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

try:
    # 這是最保險的做法：直接抓取清單中第一個支援生成內容的模型
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    
    if available_models:
        # 優先使用 flash 版 (比較快)，如果沒有就用清單第一個
        model_to_use = next((m for m in available_models if 'flash' in m), available_models[0])
        ai_model = genai.GenerativeModel(model_to_use)
        # st.success(f"成功連結 AI 模型：{model_to_use}") # 測試時可以取消註解確認
    else:
        st.error("您的 API Key 權限尚未開啟模型存取，請檢查 Google AI Studio。")
except Exception as e:
    st.error(f"AI 初始化失敗: {e}")

# --- 標題與流程說明 ---
st.markdown("<h1 style='text-align: center;'>📄 柏宇的 AI PDF 學習空間</h1>", unsafe_allow_html=True)
st.markdown("### 🚀 三步驟快速上手")
col1, col2, col3 = st.columns(3)
with col1: st.info("#### 1. 設定密碼\n你可以自訂自己的存取碼，不限字數與格式。")
with col2: st.info("#### 2. 上傳 PDF\n自動雲端儲存後將製成網站。")
with col3: st.info("#### 3. AI 筆記\nPDF可一鍵產生約300字的重點摘要。")
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

# --- 第一部分：上傳區 ---
st.subheader("📤 上傳新檔案")
uploaded_file = st.file_uploader("選擇 PDF 檔案", type=["pdf"])

# 初始化一個 session_state 來儲存剛上傳的連結
if "last_upload_url" not in st.session_state:
    st.session_state.last_upload_url = None

if uploaded_file:
    if st.button("🚀 開始上傳"):
        with st.spinner("上傳中..."):
            try:
                custom_name = uploaded_file.name
                
                # 執行上傳並取得回傳結果
                upload_result = cloudinary.uploader.upload(
                    uploaded_file, 
                    resource_type = "raw", 
                    folder = user_path,
                    public_id = custom_name
                )
                
                # 將生成的連結存入 session_state
                st.session_state.last_upload_url = upload_result['secure_url']
                
                st.success(f"✅ 上傳成功！")
                # 這裡不使用 st.rerun()，或是延遲重整，以便讓連結顯示出來
                # 如果你想讓連結留著，我們就不要在這裡馬上重整
                
            except Exception as e:
                st.error(f"上傳失敗: {e}")

# ✨ 在按鈕下方直接呈現剛生成的連結
if st.session_state.last_upload_url:
    st.info("🔗 剛上傳的檔案連結：")
    st.code(st.session_state.last_upload_url)
    st.markdown(f"[點此直接開啟檔案]({st.session_state.last_upload_url})")
    
    if st.button("🔄 重新整理檔案櫃清單"):
        st.rerun()


# --- 第二部分：個人檔案清單與 AI 功能 ---
st.subheader("📂 我的私有檔案清單")


def get_pdf_text(url):
    """從 URL 下載 PDF 並讀取文字"""
    response = requests.get(url)
    f = io.BytesIO(response.content)
    reader = PdfReader(f)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

try:
    resources = cloudinary.api.resources(type="upload", resource_type="raw", prefix=f"{user_path}/")
    file_list = resources.get("resources", [])
    
    if not file_list:
        st.write("目前尚無檔案。")
    else:
        for file in file_list:
            display_name = file['public_id'].split('/')[-1]
            file_url = file['secure_url']
            
            with st.expander(f"📄 {display_name}"):
                st.code(file_url)
                
                # 1. AI 分析按鈕
                if st.button(f"🤖 產生 AI 筆記", key=f"ai_{file['public_id']}"):
                    with st.spinner("AI 正在覽閱中..."):
                        try:
                            pdf_text = get_pdf_text(file_url)
                            if len(pdf_text) < 10:
                                st.error("注意：這份PDF檔案AI讀不到文字！請上傳正確的PDF檔案。請勿上傳JPG或PNG檔案")
                            else:
                                prompt = f"你是一個專業的讀書筆記專家。請針對以下 PDF 內容進行分析，並用繁體中文提供：\n1. 核心摘要 (300字內)\n2. 5 個關鍵知識點\n3. 適合學生的複習建議\n\n內容如下：\n{pdf_text[:10000]}"
                                response = ai_model.generate_content(prompt)
                                st.markdown("---")
                                st.markdown("### 📝 AI 學習筆記內容")
                                st.write(response.text)
                        except Exception as ai_err:
                            st.error(f"AI 分析失敗: {ai_err}")
                
                # 2. 開啟檔案連結
                st.markdown(f"[🔗 直接開啟檔案]({file_url})")
                
                # 3. 刪除功能 (放在同一個 expander 裡面)
                st.markdown("---")
                st.subheader("⚠️刪除檔案連結網站⚠️")
                
                # 安全鎖：勾選框
                confirm_delete = st.checkbox(f"我確定要刪除此檔案連結", key=f"check_{file['public_id']}")
                
                if confirm_delete:
                    if st.button(f"🔥 確定永久刪除", key=f"btn_{file['public_id']}"):
                        try:
                            result = cloudinary.uploader.destroy(
                                file['public_id'], 
                                resource_type="raw"
                            )
                            if result.get("result") == "ok":
                                st.success("✅ 檔案已成功刪除！")
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error(f"❌ 刪除失敗：{result.get('result')}")
                        except Exception as e:
                            st.error(f"❌ 發生錯誤: {e}")

except Exception as e:
    st.error(f"讀取失敗：{e}")