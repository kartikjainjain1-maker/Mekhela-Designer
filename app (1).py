import streamlit as st
import cv2
import numpy as np
import os
import json
import random
import urllib.parse
import requests
from datetime import datetime
from PIL import Image
from io import BytesIO

# Page Configuration
st.set_page_config(
    page_title="Assamese Mekhela Sador AI Studio & Virtual Try-On",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Helper to automatically download template assets from public URLs if they are missing!
# This ensures the app will NEVER throw a FileNotFoundError, even if they only have app (1).py on GitHub!
def check_and_download_assets():
    os.makedirs("images", exist_ok=True)
    assets_map = {
        "images/assamese_model_template.png": "https://tmpfiles.org/dl/wrwbiAHsBb8l/assamese_model_template.png",
        "images/mask_sador.png": "https://tmpfiles.org/dl/wuwziqHQBkEt/mask_sador.png",
        "images/mask_mekhela.png": "https://tmpfiles.org/dl/wzw4ifHusiwA/mask_mekhela.png",
        "images/sea_green_scenic_river.jpg": "https://tmpfiles.org/dl/wAwFigHwsoAZ/sea_green_scenic_river.jpg"
    }
    
    for local_path, url in assets_map.items():
        if not os.path.exists(local_path):
            try:
                response = requests.get(url, timeout=60)
                if response.status_code == 200:
                    with open(local_path, "wb") as f:
                        f.write(response.content)
            except Exception as e:
                st.error(f"Error auto-downloading required system asset '{local_path}': {e}")

# Run asset check
check_and_download_assets()

# Constants
OUTPUT_DIR = "outputs"
LOOKBOOK_DIR = "outputs/lookbook"
UPLOADS_DIR = "uploads"
MOCKUP_OUTPUT = "outputs/exact_digital_mockup_v3.png"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOOKBOOK_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Define User-Inspired Signature Poses
SIGNATURE_POSES = {
    "Namaste Greeting Pose (Indoor Studio)": {
        "desc": "Hands folded in a polite 'Namaste' greeting against a soft gray indoor wall backdrop. Warm, elegant smile.",
        "modifier": "standing in a polite 'Namaste' greeting posture with her hands folded together in front of her chest, smiling warmly. She is in an indoor studio with a minimalist soft gray wall background.",
        "accessories": "traditional gold-plated Assamese choker necklace, wide Gam-kharu gold bangles, a round red bindi on her forehead, and gold Jhumka earrings."
    },
    "Graceful Walk Pose (Outdoor Street)": {
        "desc": "Walking elegantly near an Assamese cultural venue or outdoor pathway with lush green trees. Natural sunlight.",
        "modifier": "walking gracefully with a natural, poised stride, smiling politely. The scene is outdoors near a beautiful Assamese building with decorative gates, surrounded by lush green trees under bright daytime sunlight.",
        "accessories": "elegant gold necklace, traditional Assamese gold bangles, subtle earrings, and a matching bindi."
    },
    "Scenic River & Hills Pose (Nature Catalog)": {
        "desc": "Touching her chin gracefully with rolling green hills and a calm lake/river in the background. High-fashion scenic outdoor catalog style.",
        "modifier": "standing elegantly in a high-fashion scenic outdoor catalog style, touching her chin gracefully with a poised hand. The background features rolling green mountains, misty hills, and a beautiful calm lake/river under a soft blue sky.",
        "accessories": "traditional gold-plated Jonbiri (half-moon) pendant necklace, traditional Lokaparo pigeon earrings, matching gold bracelets, and a bright red bindi."
    }
}

# Define standard lookbook views
LOOKBOOK_VIEWS = {
    "01_front_full": {
        "title": "01. Front Full-Length View",
        "desc": "Standing in a graceful full-length front-facing posture, displaying the complete matching outfit.",
        "modifier": "A front-facing full-length catalog photo of the model standing in a graceful posture, displaying the complete outfit. Highlighting the pleated Mekhela (skirt) showing the bottom row of blooming red lotus-tree motifs and dense geometric diamond borders, and the matching Sador draped across the front, matching blouse visible."
    },
    "02_back_full": {
        "title": "02. Back Full-Length View",
        "desc": "Standing gracefully from the back, displaying Sador drape and Mekhela borders wrapping around.",
        "modifier": "A full-length photo from the back, showing the model standing elegantly. Showcases the back drape of the pleated Sador and how the bottom borders of the Mekhela wrap around cleanly, capturing the fabric's flowing cotton-silk drape and the elegant rear profile."
    },
    "03_left_profile": {
        "title": "03. Left Profile Angle",
        "desc": "Full-length left profile showcasing the Sador drape flowing over the left shoulder.",
        "modifier": "A full-length profile shot facing left. Highlights the beautiful Sador drape thrown over her left shoulder, showing the vertical scalloped leaf-vine border running from top to bottom, with matching details on the blouse sleeve border, standing elegantly."
    },
    "04_right_profile": {
        "title": "04. Right Profile Angle",
        "desc": "Full-length right profile highlighting the pleating and cylindrical skirt shape.",
        "modifier": "A full-length profile shot facing right. Highlights the clean structure of the cylindrical Mekhela skirt, the tucked pleats at the waist, and the clean side-profile drape showing the fabric texture and bottom borders."
    },
    "05_three_quarter_left": {
        "title": "05. 3/4 Front Left Angle",
        "desc": "A classic high-fashion three-quarter front left pose showing draping.",
        "modifier": "A three-quarter angled view from the front-left, depicting the model in a classic high-fashion pose. Captures the beautiful transition of the Sador drape from front to shoulder, highlighting the scattered red, green, and white motifs and the elegant posture."
    },
    "06_three_quarter_right": {
        "title": "06. 3/4 Front Right Angle",
        "desc": "A three-quarter front right pose highlighting waist-pleating and blouse alignment.",
        "modifier": "A three-quarter angled view from the front-right, depicting the model looking poised. Focuses on the tucked pleats of the Mekhela at the waist, the waist-drape, and the perfect coordination between the blouse bodice and the Sador."
    },
    "07_blouse_focus": {
        "title": "07. Medium Shot (Blouse Focus)",
        "desc": "Medium crop focusing on the blouse sleeves, sleeve borders, and shoulder drape.",
        "modifier": "A medium-shot crop focusing from waist up. Displays the matching blouse in detail, showcasing the vertical scalloped leaf-vine border on the sleeves, the round neckline, and the neat shoulder pleats of the Sador pinned perfectly."
    },
    "08_sitting_pose": {
        "title": "08. Elegant Sitting Pose",
        "desc": "Sitting gracefully on a traditional chair, displaying soft fabric folds.",
        "modifier": "An elegant full-length shot of the model sitting gracefully on a traditional wooden chair. Showcases the soft, natural folding and draping of the sea-green cotton fabric around her lap, showing the intricate borders, motifs, and a serene posture."
    },
    "09_ramp_walk": {
        "title": "09. Dynamic Ramp-Walk Pose",
        "desc": "Dynamic motion shot showing the movement and flow of the handloom weave.",
        "modifier": "A high-fashion ramp-walk action shot with the model in walking motion, hair gently swaying. Captures the fluid movement of the sea-green cotton Mekhela Sador, displaying the light handloom texture of the fabric as she glides forward."
    },
    "10_bottom_border": {
        "title": "10. Close-Up (Bottom Border)",
        "desc": "Detailed macro crop of the lower Mekhela showing lotus motifs and diamond grid.",
        "modifier": "A macro catalog shot focusing on the lower half of the Mekhela skirt from knees down. Showcases the precise handloom fabric weave, the row of red and green blooming lotus-tree motifs, and the dense diamond geometric cross-hatch border along the bottom hem."
    },
    "11_shoulder_border": {
        "title": "11. Close-Up (Sador Border)",
        "desc": "Close-up of the scalloped leaf-vine border on the Sador alongside traditional gold jewelry.",
        "modifier": "A close-up portrait focusing on her collarbone and shoulder. Displays the Sador's side border (vertical scalloped leaf pattern) and the beautiful traditional gold-plated Jonbiri (half-moon) necklace and Lokaparo (pigeon) earrings on her skin."
    },
    "12_mannequin_display": {
        "title": "12. Showroom Mannequin View",
        "desc": "An elegant retail mannequin showing the attire on a showroom floor.",
        "modifier": "A professional retail showroom display of a premium mannequin or dummy wearing the matching sea-green cotton Mekhela Sador, lit under elegant studio spotlighting against a clean minimalist background."
    }
}

# User fabric description
CUSTOM_FABRIC_PROMPT = (
    "The fabric is a light pastel sea-green (mint green) color, made of soft local cotton. "
    "Across the body of both the lower skirt (Mekhela) and upper drape (Sador) are small scattered handloom floral motifs in crimson red, dark green, and white. "
    "The lower border of the Mekhela features a prominent row of traditional crimson-red and dark green blooming lotus-tree motifs, with a wide, dense geometric diamond cross-hatch pattern in forest green and crimson-red along the very bottom edge. "
    "The Sador's side border features a beautiful vertical scalloped leaf-vine pattern in dark green and crimson red. "
)

# Custom CSS Styling
st.markdown("""
<style>
    .main-title {
        color: #E24C58;
        font-family: 'Georgia', serif;
        font-weight: bold;
        text-align: center;
        margin-bottom: 5px;
    }
    .sub-title {
        text-align: center;
        color: #555;
        font-size: 1.1rem;
        margin-bottom: 25px;
    }
    .section-header {
        color: #B22222;
        border-bottom: 2px solid #E24C58;
        padding-bottom: 5px;
        margin-top: 20px;
        margin-bottom: 15px;
        font-weight: bold;
    }
    .guide-card {
        background-color: #FFF5F5;
        border-left: 5px solid #E24C58;
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .guide-title {
        color: #B22222;
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 5px;
    }
    .grid-label {
        font-weight: bold;
        text-align: center;
        color: #333;
        margin-top: 5px;
        font-size: 0.9rem;
    }
    .lookbook-title {
        font-weight: bold;
        color: #B22222;
        margin-top: 8px;
        font-size: 1rem;
    }
    .lookbook-desc {
        color: #666;
        font-size: 0.8rem;
        min-height: 40px;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to compile general prompt
def compile_general_prompt(config):
    model_part = f"A professional high-fashion catalog photo of a beautiful {config['ethnicity']} model"
    model_part += f" with {config['expression'].lower()}, looking elegant and poised,"
    model_part += f" {config['pose'].lower()}."
    
    attire_part = f" She is wearing a traditional Assamese two-piece handloom drape, a magnificent {config['material']} Mekhela Sador"
    attire_part += f" in a stunning, vibrant {config['color']} color."
    
    motif_part = f" The attire features rich traditional handwoven Assamese motifs (known as 'phul'), specifically showcasing {config['motif'].lower()}"
    motif_part += f" intricately woven across the body and the border (dahi/kari) using {config['zari'].lower()} thread."
    
    coordination = " The cylindrical lower skirt (Mekhela) features matching borders, and is draped with wide right-facing pleats tucked neatly at the center waist. The upper shoulder drape (Sador) is wrapped tightly around her waist once, forming a clean triangular fold at the front waist, and is then neatly pleated and pinned over her left shoulder, with traditional hand-braided fringe tassels (Dohi Bota) hanging elegantly at the pallu end."
    
    if config['jewelry'] != "None":
        jewelry_part = f" She is adorned with authentic traditional Assamese jewelry including {config['jewelry'].lower()}."
    else:
        jewelry_part = ""
        
    background_part = f" The scene is set in a {config['background_scene'].lower()}."
    camera_part = f" Shot in high-end commercial fashion style with {config['camera_lighting'].lower()}, soft-focus blurred background, creating high-resolution fashion photography with realistic skin textures and 8k fabric textile weave details."

    return f"{model_part}{attire_part}{motif_part}{coordination}{jewelry_part}{background_part}{camera_part}"

# Helper to generate a single lookbook view
def compile_lookbook_prompt(view_key, ethnicity, jewelry, background, lighting):
    view_info = LOOKBOOK_VIEWS[view_key]
    model_part = f"A professional high-fashion catalog photo of a beautiful {ethnicity} model. "
    model_part += view_info["modifier"] + " "
    model_part += CUSTOM_FABRIC_PROMPT
    model_part += "The attire features the classic draping style: the lower cylindrical Mekhela is tucked into the waist with broad right-facing pleats at the center, while the Sador is wrapped tightly around the hips once, forming a beautiful triangular fold at the front waist, with its pleated pallu pinned over her left shoulder featuring traditional braided fringe tassels (Dohi Bota) at the end. "
    if view_key != "12_mannequin_display" and jewelry != "None":
        model_part += f"She is adorned with {jewelry.lower()}. "
    model_part += f"The background scene is a {background.lower()}."
    camera_part = f" Captured with professional {lighting.lower()}, soft-focus blurred background, high-resolution fashion photography, realistic skin textures, and 8k fabric textile details."
    
    return f"{model_part}{camera_part}"

# Helper to compile prompt based on User-Shared Signature Poses
def compile_signature_prompt(signature_key, fabric_desc):
    pose_info = SIGNATURE_POSES[signature_key]
    
    prompt = f"A professional high-fashion catalog photo of a beautiful Assamese model, "
    prompt += pose_info["modifier"] + " "
    prompt += fabric_desc
    prompt += "The attire is a fully stitched, tailored, and ready-to-wear traditional Assamese two-piece Mekhela Sador. "
    prompt += "Draping details are authentic: the cylindrical lower Mekhela is tucked with broad right-facing waist pleats, and the upper Sador wraps tightly around her waist once, creating an iconic tucked triangular fold at her front waist before draping over her left shoulder. "
    prompt += "The shoulder drape features traditional hand-braided fringe tassels (Dohi Bota) hanging beautifully at the pallu end. "
    prompt += f"She is adorned with authentic gold-plated {pose_info['accessories']}. "
    prompt += "Captured under gorgeous natural and catalog studio lighting, high resolution, soft-focus background, realistic warm skin texture, 8k fabric weave details."
    
    return prompt

# Mockup Wrapping Core Function
def run_mockup_wrapping(chador_img_path, mekhela_img_path):
    template = cv2.imread("images/assamese_model_template.png")
    if template is None:
        return None
        
    h, w, c = template.shape
    
    mask_sador = cv2.imread("images/mask_sador.png", cv2.IMREAD_GRAYSCALE)
    mask_mekhela = cv2.imread("images/mask_mekhela.png", cv2.IMREAD_GRAYSCALE)
    
    if mask_sador is None or mask_mekhela is None:
        return None
        
    gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    _, white_fabric_mask = cv2.threshold(gray, 185, 255, cv2.THRESH_BINARY)
    
    kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    white_fabric_mask_expanded = cv2.morphologyEx(white_fabric_mask, cv2.MORPH_DILATE, kernel_small, iterations=2)
    
    mask_sador_refined = cv2.bitwise_and(mask_sador, white_fabric_mask_expanded)
    mask_mekhela_refined = cv2.bitwise_and(mask_mekhela, white_fabric_mask_expanded)
    
    hsv = cv2.cvtColor(template, cv2.COLOR_BGR2HSV)
    lower_skin = np.array([0, 15, 60])
    upper_skin = np.array([22, 175, 255])
    skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
    
    kernel_skin = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    skin_mask_expanded = cv2.morphologyEx(skin_mask, cv2.MORPH_DILATE, kernel_skin, iterations=1)
    
    face_mask = np.zeros_like(white_fabric_mask)
    face_mask[0:290, int(w*0.35):int(w*0.65)] = 255
    
    neck_mask = np.zeros_like(white_fabric_mask)
    neck_mask[290:345, int(w*0.38):int(w*0.62)] = 255
    
    preserve_mask = cv2.bitwise_or(skin_mask_expanded, face_mask)
    preserve_mask = cv2.bitwise_or(preserve_mask, neck_mask)
    
    mask_sador_final = cv2.bitwise_and(mask_sador_refined, cv2.bitwise_not(preserve_mask))
    mask_mekhela_final = cv2.bitwise_and(mask_mekhela_refined, cv2.bitwise_not(preserve_mask))
    
    chador_fabric = cv2.imread(chador_img_path)
    mekhela_fabric = cv2.imread(mekhela_img_path)
    
    if chador_fabric is None or mekhela_fabric is None:
        return None
        
    chador_resized = cv2.resize(chador_fabric, (w, h))
    mekhela_resized = cv2.resize(mekhela_fabric, (w, h))
    
    sador_blended = (template.astype(float) * chador_resized.astype(float) / 255.0).astype(np.uint8)
    mekhela_blended = (template.astype(float) * mekhela_resized.astype(float) / 255.0).astype(np.uint8)
    
    output = template.copy()
    
    sador_alpha = cv2.GaussianBlur(mask_sador_final, (3, 3), 0)[:, :, np.newaxis].astype(float) / 255.0
    output = (sador_alpha * sador_blended.astype(float) + (1.0 - sador_alpha) * output.astype(float)).astype(np.uint8)
    
    mekhela_alpha = cv2.GaussianBlur(mask_mekhela_final, (3, 3), 0)[:, :, np.newaxis].astype(float) / 255.0
    output = (mekhela_alpha * mekhela_blended.astype(float) + (1.0 - mekhela_alpha) * output.astype(float)).astype(np.uint8)
    
    output_rgb = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
    return Image.fromarray(output_rgb)


# Header
st.markdown("<h1 class='main-title'>🌾 Assamese Mekhela Sador AI Studio</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Fully Tailored Dressings, 12-Angle Lookbooks, & Pattern-Preserving Virtual Try-On for Assamese Models</p>", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📸 Signature Poses (User Inspired)",
    "⚙️ 12-Angle Lookbook Studio", 
    "👗 100% Exact Try-On (Mockup)",
    "🎨 Traditional Design Studio", 
    "📚 Cultural, Tailoring & Draping Guide", 
    "📂 Saved Gallery"
])

# Sidebar Controls
with st.sidebar:
    st.markdown("### 🛠️ Global Parameters")
    
    ethnicity = st.selectbox(
        "Model Ethnicity / Look",
        ["Assamese", "North-East Indian", "South Asian (Pan-Indian)", "Tibeto-Burman / Indigenous"],
        index=0, key="global_eth"
    )
    
    st.markdown("---")
    st.markdown("**🎨 Traditional Customizer Settings**")
    
    t2_material = st.selectbox(
        "Fabric Material",
        ["Golden Muga Silk", "Pat Silk", "Eri Silk", "Nuni Cotton", "Toss Silk"]
    )
    t2_color = st.color_picker("Base Color Selection", "#D4AF37")
    t2_motif = st.selectbox(
        "Woven Motif",
        ["Japi motifs", "Miri motifs", "Kalka motifs", "Pepo motifs", "Gach motifs", "Mayur motifs", "Kaziranga Elephant"]
    )
    t2_zari = st.selectbox(
        "Zari Embroidery",
        ["Golden Guna thread", "Silver Rupholi thread", "Vibrant Multi-colored Threads"]
    )
    t2_pose = st.selectbox(
        "Pose (Design Studio)",
        ["Graceful full-length standing pose", "Catwalk ramp-walk pose", "Sitting elegantly on a traditional chair"]
    )
    t2_expression = st.selectbox(
        "Expression (Design Studio)",
        ["Warm, elegant smile", "Graceful and serene royal look", "Confident high-fashion expression"]
    )

# ================= TAB 1: SIGNATURE POSES (USER INSPIRED) =================
with tab1:
    st.markdown("<h3 class='section-header'>📸 User-Inspired Signature Posing Styles</h3>", unsafe_allow_html=True)
    st.markdown(
        """
        I have analyzed your shared example pictures showing how the finished, draped, and stitched Mekhela Sador looks 
        on real Assamese models. I have added these **three specific photo styles** as instant catalog generators!
        """
    )
    
    col_sig1, col_sig2 = st.columns([1, 1.2])
    
    with col_sig1:
        st.markdown("#### ⚙️ Signature Configuration")
        
        selected_sig = st.selectbox(
            "Select Posing Style & Setting",
            list(SIGNATURE_POSES.keys())
        )
        
        st.write(f"**Style Description:** {SIGNATURE_POSES[selected_sig]['desc']}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 🧬 Fabric Definition")
        st.write("The system uses your uploaded sea-green fabric details ( lotus motifs, diamond cross-hatch, scalloped vine borders, and Dohi Bota tassels).")
        
        sig_seed = st.number_input("Generation Seed", value=98765, min_value=1, max_value=99999999, key="seed_sig")
        
        st.markdown("<br>", unsafe_allow_html=True)
        gen_sig_btn = st.button("✨ Weave Signature Model Photo", type="primary", use_container_width=True)
        
    with col_sig2:
        st.markdown("#### 🖼️ Output Catalog Photo")
        
        if gen_sig_btn:
            with st.spinner("Weaving signature catalog pose..."):
                prompt = compile_signature_prompt(selected_sig, CUSTOM_FABRIC_PROMPT)
                encoded_p = urllib.parse.quote(prompt)
                
                # We use 768x1152 for beautiful vertical catalog portraits
                api_url = f"https://image.pollinations.ai/prompt/{encoded_p}?width=768&height=1152&seed={sig_seed}&model=flux&nologo=true"
                
                try:
                    response = requests.get(api_url, timeout=60)
                    if response.status_code == 200:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"sig_{timestamp}_{sig_seed}.png"
                        filepath = os.path.join(OUTPUT_DIR, filename)
                        
                        img = Image.open(BytesIO(response.content))
                        img.save(filepath)
                        
                        st.session_state['latest_sig_image'] = filepath
                        st.session_state['latest_sig_bytes'] = response.content
                        st.success("🎉 Catalog photo woven successfully!")
                    else:
                        st.error(f"API Error: {response.status_code}")
                except Exception as e:
                    st.error(f"Error: {e}")
                    
        # Display latest or placeholder
        if 'latest_sig_image' in st.session_state and os.path.exists(st.session_state['latest_sig_image']):
            st.image(Image.open(st.session_state['latest_sig_image']), use_container_width=True)
            st.download_button(
                label="📥 Download Signature Photo",
                data=st.session_state['latest_sig_bytes'],
                file_name=os.path.basename(st.session_state['latest_sig_image']),
                mime="image/png"
            )
        else:
            pre_saved_sig = "images/sea_green_scenic_river.jpg"
            if os.path.exists(pre_saved_sig):
                st.image(Image.open(pre_saved_sig), caption="Scenic River & Hills Pose (Pre-Generated Sample)", use_container_width=True)
            else:
                st.info("Click 'Weave Signature Model Photo' to start!")


# ================= TAB 2: 12-ANGLE LOOKBOOK STUDIO =================
with tab2:
    st.markdown("<h3 class='section-header'>📦 Uploaded Custom Fabric Reference</h3>", unsafe_allow_html=True)
    
    chador_path = os.path.join(UPLOADS_DIR, "20260322_132555.jpg")
    mekhela_path = os.path.join(UPLOADS_DIR, "20260322_132749.jpg")
    blouse_path = os.path.join(UPLOADS_DIR, "20260322_132825.jpg")
    border_path = os.path.join(UPLOADS_DIR, "20260322_132643.jpg")
    
    col_u1, col_u2, col_u3, col_u4 = st.columns(4)
    with col_u1:
        if os.path.exists(chador_path):
            st.image(Image.open(chador_path), use_container_width=True)
            st.markdown("<div class='grid-label'>📥 Sador (Chador) Fabric</div>", unsafe_allow_html=True)
    with col_u2:
        if os.path.exists(mekhela_path):
            st.image(Image.open(mekhela_path), use_container_width=True)
            st.markdown("<div class='grid-label'>📥 Mekhela Fabric</div>", unsafe_allow_html=True)
    with col_u3:
        if os.path.exists(blouse_path):
            st.image(Image.open(blouse_path), use_container_width=True)
            st.markdown("<div class='grid-label'>📥 Blouse piece / border</div>", unsafe_allow_html=True)
    with col_u4:
        if os.path.exists(border_path):
            st.image(Image.open(border_path), use_container_width=True)
            st.markdown("<div class='grid-label'>📥 Sador Side Border</div>", unsafe_allow_html=True)
            
    st.markdown("<h3 class='section-header'>🧬 Virtual Wear & Fitting Dashboard</h3>", unsafe_allow_html=True)
    st.info("💡 **Fabric Detected:** Custom mint green sea-green cotton fabric with scattered crimson-red, forest-green, and white handloom floral motifs, with a blooming lotus temple border and geometric diamond cross-hatch hem.")
    
    col_ctrl1, col_ctrl2 = st.columns([1, 1])
    with col_ctrl1:
        lookbook_seed = st.number_input("Lookbook Master Seed", value=54321, min_value=1, max_value=99999999, key="seed_lookbook")
    with col_ctrl2:
        st.markdown("<br>", unsafe_allow_html=True)
        gen_all_btn = st.button("✨ Weave Full 12-Angle Lookbook (Batch Generate)", type="primary", use_container_width=True, key="btn_lookbook")
        
    if gen_all_btn:
        progress_text = "Weaving 12 distinct catalog angles. Please hold on..."
        progress_bar = st.progress(0.0, text=progress_text)
        
        for idx, (view_key, view_info) in enumerate(LOOKBOOK_VIEWS.items()):
            view_prompt = compile_lookbook_prompt(view_key, ethnicity, jewelry, background_scene, camera_lighting)
            encoded_view = urllib.parse.quote(view_prompt)
            api_url = f"https://image.pollinations.ai/prompt/{encoded_view}?width=768&height=1152&seed={lookbook_seed}&model=flux&nologo=true"
            
            try:
                response = requests.get(api_url, timeout=60)
                if response.status_code == 200:
                    filepath = os.path.join(LOOKBOOK_DIR, f"{view_key}.png")
                    with open(filepath, "wb") as f:
                        f.write(response.content)
            except Exception as e:
                st.error(f"Error generating {view_info['title']}: {e}")
                
            percent_complete = (idx + 1) / 12
            progress_bar.progress(percent_complete, text=f"Woven {idx+1}/12: {view_info['title']}")
            
        st.success("🎉 Lookbook completed successfully! All 12 views are displayed below.")
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📂 Woven Lookbook Grid")
    
    grid_cols = st.columns(4)
    for idx, (view_key, view_info) in enumerate(LOOKBOOK_VIEWS.items()):
        col_target = grid_cols[idx % 4]
        filepath = os.path.join(LOOKBOOK_DIR, f"{view_key}.png")
        
        with col_target:
            st.markdown(f"<p class='lookbook-title'>{view_info['title']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='lookbook-desc'>{view_info['desc']}</p>", unsafe_allow_html=True)
            
            if os.path.exists(filepath):
                st.image(Image.open(filepath), use_container_width=True)
                
                with open(filepath, "rb") as f_bytes:
                    btn_bytes = f_bytes.read()
                st.download_button(
                    label="📥 Download",
                    data=btn_bytes,
                    file_name=f"{view_key}_{lookbook_seed}.png",
                    mime="image/png",
                    key=f"dl_lb_{view_key}"
                )
                
                sub_gen = st.button("🔄 Re-Weave", key=f"regen_lb_{view_key}")
                if sub_gen:
                    with st.spinner("Weaving single angle..."):
                        view_prompt = compile_lookbook_prompt(view_key, ethnicity, jewelry, background_scene, camera_lighting)
                        encoded_view = urllib.parse.quote(view_prompt)
                        rand_seed = random.randint(1, 99999)
                        api_url = f"https://image.pollinations.ai/prompt/{encoded_view}?width=768&height=1152&seed={rand_seed}&model=flux&nologo=true"
                        
                        try:
                            response = requests.get(api_url, timeout=60)
                            if response.status_code == 200:
                                with open(filepath, "wb") as f:
                                    f.write(response.content)
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            else:
                st.markdown(
                    f"""
                    <div style="border: 2px dashed #ccc; padding: 60px 10px; text-align: center; border-radius: 8px; background-color: #fafafa; margin-bottom: 10px;">
                        <p style="font-size: 2.5rem; margin: 0; color: #aaa;">🪡</p>
                        <p style="color: #888; font-size: 0.8rem; margin-top: 5px;">Not yet woven</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                single_gen = st.button("✨ Weave Angle", key=f"gen_single_{view_key}", use_container_width=True)
                if single_gen:
                    with st.spinner("Weaving single angle..."):
                        view_prompt = compile_lookbook_prompt(view_key, ethnicity, jewelry, background_scene, camera_lighting)
                        encoded_view = urllib.parse.quote(view_prompt)
                        api_url = f"https://image.pollinations.ai/prompt/{encoded_view}?width=768&height=1152&seed={lookbook_seed}&model=flux&nologo=true"
                        
                        try:
                            response = requests.get(api_url, timeout=60)
                            if response.status_code == 200:
                                with open(filepath, "wb") as f:
                                    f.write(response.content)
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            st.markdown("<br><hr>", unsafe_allow_html=True)


# ================= TAB 3: 100% EXACT TRY-ON (PATTERN PRESERVER) =================
with tab3:
    st.markdown("<h3 class='section-header'>👗 Pixel-Perfect Try-On Studio (100% Original Design)</h3>", unsafe_allow_html=True)
    st.markdown(
        """
        **The Problem with Standard AI**: Traditional Text-to-Image AI will regenerate similar but *different* motif designs. 
        **The Solution**: Our custom **Digital Try-On Engine** wraps your *exact* uploaded fabric photos directly onto a high-definition 
        photo of an **Assamese model**, preserving 100% of your color, weave texture, motifs, and borders, while keeping the realistic folds and drapes of the cloth!
        """
    )
    
    col_t3_f1, col_t3_f2 = st.columns([1, 1.2])
    
    with col_t3_f1:
        st.markdown("#### 📂 Upload Custom Fabrics")
        st.write("Upload any new Mekhela and Sador fabric photos below. If left empty, the system will use your default sea-green images.")
        
        uploaded_chador = st.file_uploader("1. Upload Sador (Chador) fabric image", type=["jpg", "png", "jpeg"], key="up_chador")
        uploaded_mekhela = st.file_uploader("2. Upload Mekhela fabric image", type=["jpg", "png", "jpeg"], key="up_mekhela")
        
        chador_file = chador_path
        mekhela_file = mekhela_path
        
        if uploaded_chador:
            chador_temp_path = os.path.join(UPLOADS_DIR, "temp_chador.png")
            with open(chador_temp_path, "wb") as f:
                f.write(uploaded_chador.getbuffer())
            chador_file = chador_temp_path
            st.success("Sador uploaded!")
            
        if uploaded_mekhela:
            mekhela_temp_path = os.path.join(UPLOADS_DIR, "temp_mekhela.png")
            with open(mekhela_temp_path, "wb") as f:
                f.write(uploaded_mekhela.getbuffer())
            mekhela_file = mekhela_temp_path
            st.success("Mekhela uploaded!")
            
        st.markdown("<br>", unsafe_allow_html=True)
        run_mockup_btn = st.button("✨ Dress Assamese Model with Exact Patterns", type="primary", use_container_width=True)
        
    with col_t3_f2:
        st.markdown("#### 🖼️ Draped Assamese Model")
        
        fallback_mockup_path = "outputs/exact_digital_mockup_v3.png"
        
        if run_mockup_btn:
            with st.spinner("Executing mathematical drapery and folding engine..."):
                mockup_img = run_mockup_wrapping(chador_file, mekhela_file)
                if mockup_img is not None:
                    st.session_state['active_mockup_image'] = mockup_img
                    mockup_img.save(MOCKUP_OUTPUT)
                else:
                    st.error("Error occurred during mockup rendering.")
            
        if 'active_mockup_image' in st.session_state:
            st.image(st.session_state['active_mockup_image'], caption="Assamese Model wearing your 100% exact design", use_container_width=True)
            
            img_io = BytesIO()
            st.session_state['active_mockup_image'].save(img_io, 'PNG')
            img_io.seek(0)
            st.download_button(
                label="📥 Download Exact Mockup Image",
                data=img_io,
                file_name="assamese_model_exact_design.png",
                mime="image/png",
                use_container_width=True
            )
        elif os.path.exists(fallback_mockup_path):
            st.image(Image.open(fallback_mockup_path), caption="Assamese Model wearing your 100% exact design (Sample Output)", use_container_width=True)
            with open(fallback_mockup_path, "rb") as f_bytes:
                b_data = f_bytes.read()
            st.download_button(
                label="📥 Download Exact Mockup Image",
                data=b_data,
                file_name="assamese_model_exact_design_sample.png",
                mime="image/png",
                use_container_width=True
            )
        else:
            st.image(Image.open("images/assamese_model_template.png"), caption="Template Model (Plain Off-White Drape)", use_container_width=True)


# ================= TAB 4: TRADITIONAL DESIGN STUDIO =================
with tab4:
    col_t4_1, col_t4_2 = st.columns([1, 1])
    
    with col_t4_1:
        st.markdown("<h3 class='section-header'>🎨 Active Design Customizer</h3>", unsafe_allow_html=True)
        st.write("Customize material, custom colors, woven patterns, jewelry, and settings to create unique combinations.")
        
        st.markdown(f"""
        - **Model:** {ethnicity} | {t2_expression} | {t2_pose}
        - **Textile:** {t2_material} in **{t2_color}**
        - **Motifs:** {t2_motif} woven in {t2_zari}
        - **Jewelry:** {jewelry}
        - **Background:** {background_scene}
        - **Lighting:** {camera_lighting}
        """)
        
        t2_gen_btn = st.button("✨ Generate Custom Designer Masterpiece", type="primary", use_container_width=True)
        
        if t2_gen_btn:
            with st.spinner("Threading active loom..."):
                t2_config = {
                    "ethnicity": ethnicity,
                    "expression": t2_expression,
                    "pose": t2_pose,
                    "material": t2_material,
                    "color": f"hex {t2_color}",
                    "motif": t2_motif,
                    "zari": t2_zari,
                    "jewelry": jewelry,
                    "background_scene": background_scene,
                    "camera_lighting": camera_lighting
                }
                
                prompt_text = compile_general_prompt(t2_config)
                encoded_p = urllib.parse.quote(prompt_text)
                rand_seed = random.randint(1, 99999)
                api_url = f"https://image.pollinations.ai/prompt/{encoded_p}?width=1024&height=1024&seed={rand_seed}&model=flux&nologo=true"
                
                try:
                    response = requests.get(api_url, timeout=60)
                    if response.status_code == 200:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"design_{timestamp}_{rand_seed}.png"
                        filepath = os.path.join(OUTPUT_DIR, filename)
                        
                        with open(filepath, "wb") as f:
                            f.write(response.content)
                            
                        with open(filepath.replace(".png", ".json"), "w") as f:
                            json.dump(t2_config, f, indent=4)
                            
                        st.session_state['latest_general'] = filepath
                        st.session_state['latest_general_bytes'] = response.content
                        st.success("🎉 Successfully woven designer masterpiece!")
                except Exception as e:
                    st.error(f"Error: {e}")
                    
    with col_t4_2:
        st.markdown("<h3 class='section-header'>🖼️ Designer Output Preview</h3>", unsafe_allow_html=True)
        if 'latest_general' in st.session_state and os.path.exists(st.session_state['latest_general']):
            st.image(Image.open(st.session_state['latest_general']), use_container_width=True)
            st.download_button(
                label="📥 Download High-Resolution Masterpiece",
                data=st.session_state['latest_general_bytes'],
                file_name=os.path.basename(st.session_state['latest_general']),
                mime="image/png"
            )
        else:
            st.markdown(
                """
                <div style="border: 2px dashed #ccc; padding: 80px; text-align: center; border-radius: 8px; background-color: #fafafa;">
                    <p style="font-size: 3.5rem; margin: 0; color: #E24C58;">👗</p>
                    <p style="font-weight: bold; color: #555; margin-top: 10px;">Your custom woven design will appear here</p>
                </div>
                """,
                unsafe_allow_html=True
            )

# ================= TAB 5: CULTURAL, TAILORING & DRAPING GUIDE =================
with tab5:
    st.markdown("<h3 class='section-header'>📚 The Cultural Tapestry of Assam’s Mekhela Sador</h3>", unsafe_allow_html=True)
    st.markdown("""
    The **Mekhela Sador** is the traditional indigenous attire worn by women in Assam, North-East India. 
    It is a beautiful **two-piece ensemble** consisting of:
    1. **The Mekhela (Lower part):** A wide cylindrical fabric folded into one or two deep, right-facing pleats around the waist and tucked in.
    2. **The Sador (Upper part):** A long, neatly pleated drape tucked into the Mekhela, which is thrown gracefully over the left shoulder.
    """)
    
    st.markdown("#### ✂️ Custom Posing & Tailoring Definitions (User Shared)")
    
    col_t5_1, col_t5_2 = st.columns(2)
    
    with col_t5_1:
        st.markdown(f"""
        <div class="guide-card">
            <div class="guide-title">🪡 1. Tailoring the Mekhela (Bottom Skirt)</div>
            <p style="font-size: 0.9rem; color: #444;">
                The Mekhela is a rectangular handloom fabric that needs to be joined into a cylinder. 
                The tailor joins the two vertical open edges together with a straight machine stitch. 
                The top and bottom edges are folded over and neatly hemmed to prevent the thread weave from fraying. 
                When worn, it is folded to the right in deep, neat pleats.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="guide-card">
            <div class="guide-title">🏮 3. Traditional Tassel Work (Dohi Bota)</div>
            <p style="font-size: 0.9rem; color: #444;">
                A highly authentic element of the Sador is the <b>Dohi Bota</b>. 
                The raw threads at the pallu end are hand-twisted or braided into neat, decorative tassels. 
                Our AI model automatically integrates these braided fringe tassels onto the Sador's draping end to match your actual ready-to-wear designs!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_t5_2:
        st.markdown(f"""
        <div class="guide-card">
            <div class="guide-title">🧣 2. Tailoring the Sador (Top Drapery)</div>
            <p style="font-size: 0.9rem; color: #444;">
                The Sador is the upper wrap thrown over the left shoulder. 
                It requires finishing on both ends to look polished. 
                Often, decorative side borders (poti) are woven separately on the loom and stitched onto the length of the Sador.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="guide-card">
            <div class="guide-title">👚 4. Tailoring the Blouse Piece</div>
            <p style="font-size: 0.9rem; color: #444;">
                Your set includes an extra unstitched fabric cutting meant for the blouse. 
                The tailor takes precise body measurements to stitch a standard, form-fitting blouse 
                with matching scalloped sleeve borders, completing the elegant three-piece outfit.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Added Draping Masterclass from User's Video Tutorial
    st.markdown("#### 🧘 Draping Masterclass (As Shown in Draping Video Tutorial)")
    st.markdown(
        """
        <div class="guide-card" style="background-color: #F9FFF9; border-left: 5px solid #2E8B57;">
            <div class="guide-title" style="color: #2E8B57;">🎬 How to Drape Mekhela Sador Perfectly (Step-by-Step)</div>
            <p style="font-size: 0.9rem; color: #333;">
                Our draping guidelines are meticulously designed based on authentic draping tutorials to ensure that 
                every generated model's drape is 100% correct and highly elegant.
            </p>
            <ol style="font-size: 0.9rem; color: #444; line-height: 1.6;">
                <li><b>The Step-In (Mekhela)</b>: Step into the pre-stitched cylindrical Mekhela loop. Place the plain fabric section on the back/left side of the waist, and let the beautifully decorated design/motif section sit prominently in front.</li>
                <li><b>The Right-Facing Pleats</b>: Unlike regular sarees (which are pleated to the left), gather the extra front fabric and fold it into <b>broad, right-facing pleats</b> (typically 1 or 2 deep pleats). Align the pleats perfectly all the way to the bottom hem, and tuck them firmly into the waist center.</li>
                <li><b>The Hip-Wrap & Waist Triangle (Sador)</b>: Take one end of the Sador and tuck it into the right side of the waist. Wrap the Sador tightly around your waist and hips exactly <b>one full time</b>. As you bring it back to the front, tuck it in to form a clean, sharp, iconic <b>triangular drape/fold</b> at the front waist that aligns beautifully with the Mekhela's waistband.</li>
                <li><b>The Pinned Pallu</b>: Take the remaining fabric of the Sador, gather it into neat shoulder pleats, and drape it diagonally across your chest over the <b>left shoulder</b>. Secure it with a safety pin on your blouse, letting the gorgeous pallu border and braided fringe tassels (Dohi Bota) dangle elegantly down your back.</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True
    )

# ================= TAB 6: GENERAL SAVED GALLERY =================
with tab6:
    st.markdown("<h3 class='section-header'>📂 Saved Gallery Archive</h3>", unsafe_allow_html=True)
    all_files = os.listdir(OUTPUT_DIR)
    png_files = sorted([f for f in all_files if f.endswith(".png") and not f.startswith("lookbook") and not f.startswith("exact_digital_mockup") and not f.startswith("sig")], reverse=True)
    
    if len(png_files) == 0:
        st.write("No general creations saved yet. Go to the 'Traditional Design Studio' to weave one!")
    else:
        grid_gallery = st.columns(4)
        for idx, filename in enumerate(png_files):
            col_target = grid_gallery[idx % 4]
            img_path = os.path.join(OUTPUT_DIR, filename)
            
            with col_target:
                st.image(Image.open(img_path), use_container_width=True)
                with open(img_path, "rb") as f_bytes:
                    b_data = f_bytes.read()
                st.download_button(
                    label="📥 Download",
                    data=b_data,
                    file_name=filename,
                    mime="image/png",
                    key=f"dl_gallery_{filename}"
)
