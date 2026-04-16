import streamlit as st
import cloudinary
import cloudinary.uploader
import uuid

# 從 Streamlit 的「保險箱」讀取密鑰，而不是直接寫死
cloudinary.config( 
  cloud_name = st.secrets["CLOUDINARY_NAME"], 
  api_key = st.secrets["CLOUDINARY_API_KEY"], 
  api_secret = st.secrets["CLOUDINARY_API_SECRET"],
  secure = True
)
st.title("📄 柏宇的 PDF 分享工具")
st.write("上傳 PDF 後，即可獲得分享連結。")

uploaded_file = st.file_uploader("請選擇 PDF 檔案", type=["pdf"])

if uploaded_file is not None:
    if st.button("🚀 上傳並產生連結"):
        with st.spinner("上傳中..."):
            try:
                # 執行上傳
                upload_result = cloudinary.uploader.upload(
                    uploaded_file, 
                    resource_type = "raw", 
                    public_id = f"pdfs/{uuid.uuid4()}_{uploaded_file.name}"
                )
                # 取得連結
                file_url = upload_result.get("secure_url")
                
                st.success("成功！")
                st.code(file_url)
                st.markdown(f"[🔗 按此開啟 PDF]({file_url})")
            except Exception as e:
                st.error(f"錯誤：{e}")
                