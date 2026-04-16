import streamlit as st
import cloudinary
import cloudinary.uploader
import uuid

# 填入你的 Cloudinary 鑰匙
cloudinary.config( 
  cloud_name = "dontrm57o", 
  api_key = "127411183399797", 
  api_secret = "3zitwMsjNd5ojuRgqPS3ji8Ufzc",
  secure = True
)

st.title("📄 我的 PDF 分享工具")
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
                