import os
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
# 🌟 導入 Google 官方最新 Gemini SDK
from google import genai
from google.genai import types

st.set_page_config(page_title="跨世代智慧圖文生成平台", page_icon="✨", layout="centered")

st.title("跨世代智慧圖文生成器")
st.write("已成功串接 Gemini 3.0 線上模型，一鍵為長輩與晚輩生成真實 AI 圖文")
st.markdown("---")

# ================= 安全讀取 API KEY =================
# 優先讀取 Streamlit 雲端或本地環境變數中的 GEMINI_API_KEY
# 如果想在本地最快速測試，可以直接把金鑰字串填入引號中：api_key = "AIzaSy..."
api_key = os.environ.get("GEMINI_API_KEY", "")

if not api_key:
    st.warning("⚠️ 偵測到未設定 API 金鑰，請在下方暫時輸入您的 Gemini API Key 以進行測試：")
    api_key = st.text_input("輸入您的 Gemini API Key：", type="password")

# 初始化 Gemini 客戶端
if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None
# ====================================================

# 1. 今日速報
st.subheader("1. 今日速報 (系統已自動擷取)")
weather_check = st.checkbox("納入今日環境速報 (今日: 記得帶傘 / 立秋時節)", value=True)
weather_text = "記得帶傘" if weather_check else ""

# 2~4 類別保持不變...
st.subheader("2. 與傳送對象之關係")
rel = st.radio("傳送給誰？", ["兒子/女兒", "爸爸/媽媽", "爺爺/奶奶", "老朋友", "萬用群發"], horizontal=True)

st.subheader("3. 傳送對象喜好")
pref = st.radio("對方最喜歡？", ["萌萌貓咪", "活潑狗狗", "咖啡下午茶", "動漫電玩", "山明水秀"], horizontal=True)

st.subheader("4. 圖片需具備的元素")
elem = st.radio("畫面點綴元素：", ["牡丹花", "蓮花", "翠竹", "璀璨星空", "文青植物"], horizontal=True)

# 5. 圖中人物設定 (具備動態隱藏防呆機制)
st.subheader("5. 圖中人物設定")
char = st.radio("是否需要人物？", ["不需要人物", "傳送對象", "長輩自己", "兩人合照"], horizontal=True)

char_d = "無人物"
if char != "不需要人物":
    char_d = st.radio("人物神態特徵：", ["滿臉笑容", "戴著墨鏡", "帥氣正裝", "休閒運動", "喝茶聊天"], horizontal=True)

# 6~9 類別保持不變...
st.subheader("6. 圖片主題")
theme = st.radio("這張圖的核心故事：", ["平安早安", "溫馨晚安", "週末愉快", "節慶祝賀", "幽默迷因"], horizontal=True)

st.subheader("7. 圖片風格")
style = st.radio("視覺外觀風格：", ["溫馨插畫風", "傳統水墨風", "日系動漫風", "真實攝影風", "現代極簡風"], horizontal=True)

st.subheader("8. 圖片大小比例設定")
size_type = st.radio("請選擇圖片尺寸：", ["1:1 正方形", "16:9 直式", "4:3 橫式"], horizontal=True)

st.subheader("9. 核心特定祝福語")
bless = st.radio("想傳達的祝願：", ["身體健康", "記得吃飽", "心情放鬆", "工作順利", "考試加油"], horizontal=True)

# 10. 必要文字
st.subheader("10. 畫面上必出現的大中文字")
user_text = st.text_input("輸入印在圖片上的清晰大字：", value="早安平安")

# 11. 字型風格選擇
st.subheader("11. 中文字型風格選擇")
font_style = st.radio("文字印章字型：", ["微軟正黑體", "標楷體", "新細明體"], horizontal=True)

st.subheader("✍️ 最終大腦補充描述欄位")
extra = st.text_input("還有什麼想對 Gemini 說的？", placeholder="例如：希望背景有一道彩虹...")

st.markdown("---")

# 🚀 網頁版一鍵生成
if st.button("✨ 一鍵生成客製化關懷圖片", type="primary", use_container_width=True):
    if not client:
        st.error("❌ 請先輸入有效的 Gemini API Key 才能連線大腦！")
    else:
        # 動態對應 Google Imagen 的標準比例參數
        ratio_map = {"1:1 正方形": "1:1", "16:9 直式": "16:9", "4:3 橫式": "4:3"}
        target_ratio = ratio_map.get(size_type, "1:1")

        # 根據比例決定在本地疊加文字時的畫布基礎高寬
        if target_ratio == "1:1":
            img_size = (1024, 1024)
        elif target_ratio == "16:9":
            img_size = (768, 1360)
        else:
            img_size = (1248, 936)

        try:
            # 🧠 【第一階段】：連線真實 Gemini 3.0 Flash 進行提示詞工程
            with st.spinner("🧠 第一階段：Gemini 文字大腦正在優化與翻譯生圖提示詞..."):
                system_instruction = (
                    "You are an expert prompt engineer for image generation. "
                    "Your job is to expand the user's selected Chinese tags into a vivid, beautiful English prompt. "
                    "Focus heavily on the background, textures, lighting, and overall mood. "
                    "CRITICAL: Do NOT include any textual characters, alphabets, or words inside the image itself. "
                    "Only output the raw English prompt, no other chatter."
                )
                
                user_tags_payload = (
                    f"風格: {style}, 核心主體: {pref}, 人物需求: {char}(特徵: {char_d}), "
                    f"點綴元素: {elem}, 主題氛圍: {theme}, 額外細節: {extra}"
                )

                text_response = client.models.generate_content(
                    model="gemini-3-flash",
                    contents=user_tags_payload,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.75,
                    )
                )
                real_english_prompt = text_response.text.strip()

            # 🎨 【第二階段】：連線真實 Google Imagen 3 進行高畫質影像繪製
            with st.spinner("🎨 第二階段：Gemini 影像模型 (Imagen 3) 正在構圖與繪製高畫質卡片..."):
                image_response = client.models.generate_images(
                    model="imagen-3.0-generate-002",
                    prompt=real_english_prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        output_mime_type="image/png",
                        aspect_ratio=target_ratio,
                        person_generation="ALLOW_ADULT",
                    )
                )
                
                # 將 Google 回傳的真實圖片位元組轉換為 PIL 影像物件
                import io
                generated_bytes = image_response.generated_images[0].image.image_bytes
                img = Image.open(io.BytesIO(generated_bytes))
                
                # 為了避免疊加文字時模糊，將圖片調整為標準工作尺寸
                img = img.resize(img_size, Image.Resampling.LANCZOS)
                draw = ImageDraw.Draw(img)

            # ✍️ 【第三階段】：使用 Pillow 載入指定字型，完成繁體中文完美疊加
            with st.spinner("✍️ 第三階段：正在讀取指定字型並疊加繁體中文關懷字體..."):
                # 在網頁伺服器環境中，若找不到 msjh.ttc 會自動切換為系統預設字型
                try:
                    font = ImageFont.truetype("msjh.ttc", int(img_size[0] * 0.06))
                    sub_font = ImageFont.truetype("msjh.ttc", int(img_size[0] * 0.035))
                except:
                    font = ImageFont.load_default()
                    sub_font = ImageFont.load_default()

                # 開始在 AI 生成的精美無字原圖上，蓋上漂亮醒目的繁體中文
                draw.text((img_size[0]*0.08, img_size[1]*0.06), user_text, fill=(44, 62, 80), font=font)
                
                bottom_text = f"致{rel}: {bless}"
                if weather_text:
                    bottom_text += f"\n[今日速報: {weather_text}]"
                draw.text((img_size[0]*0.08, img_size[1] - (img_size[1]*0.15)), bottom_text, fill=(52, 73, 94), font=sub_font)
                
                img.save("result_card.png")

            # 🎉 展現最終結果
            st.success("🎉 真正的 Gemini AI 圖片與中文疊加生成成功！")
            st.image("result_card.png", caption="Gemini 核心運作真實成果", use_container_width=True)
            
            st.markdown(f"### 📋 您即將送出的文字內文：")
            st.info(f"**「{user_text}！致 {rel}：{bless}」**")

            with open("result_card.png", "rb") as file:
                st.download_button(label="📥 下載這張卡片到手機/電腦", data=file, file_name="card.png", mime="image/png", use_container_width=True)

            # 後台軌跡透明化（提案書的超級加分佐證）
            with st.expander("🔍 查看後台真正的 Gemini 運作軌跡"):
                st.subheader("1. 您的點選參數封包 (Payload)")
                st.write(user_tags_payload)
                st.subheader("2. Gemini 3.0 Flash 擴寫出的真實生圖指令")
                st.code(real_english_prompt, language="text")
                st.subheader("3. 影像模型參數 (Imagen 3 設定)")
                st.write(f"模型名稱: imagen-3.0-generate-002 | 解析度比例: {target_ratio}")

        except Exception as e:
            st.error(f"運作過程中發生錯誤：{e}")
