import streamlit as st
import cv2
import tempfile
import time
from false_positive_prevention import safe_predict_video, safe_predict_image
from PIL import Image

st.set_page_config(
    page_title="Early Screen ASD",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🧠 Early Screen ASD Detection System")
st.markdown("### Early Autism Spectrum Disorder Screening & Analysis")

# Custom CSS for styling
st.markdown("""
<style>
    .reportview-container {
        background: #FFF1F2;
    }
    .stButton>button {
        color: white;
        background-color: #B42949;
        border-radius: 5px;
    }
    .stProgress .st-bo {
        background-color: #059669;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.header("📁 File Selection")
st.sidebar.image("LOGO.png", width=100)
upload_type = st.sidebar.radio("Upload format:", ("Video", "Image"))


def process_video(file_path):
    with st.spinner("Analyzing Video..."):
        # Safe Prediction Route
        res = safe_predict_video(file_path)
        if len(res) == 5:
            cls, conf, frame_preds, percentages, total_frames = res
        else:
            cls, conf, frame_preds = res[:3]
            percentages = {}
            total_frames = 0
        
        st.write("---")
        
        if cls == "Undetected":
            st.error("❌ FAILED SAFETY CHECK: No human content detected.")
            st.warning("Analysis skipped for safety to prevent false positives on screen recordings or animations.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                if conf >= 0.60:
                    st.success("✅ Valid Analysis Complete")
                    st.metric("Predicted Behavior", cls, f"{conf:.2%} Confidence")
                else:
                    st.warning("⚠️ Low Confidence")
                    st.metric("Predicted Output", cls, f"{conf:.2%} Confidence")
            
            with col2:
                st.info("System Data")
                st.write(f"**Frames Processed:** {total_frames}")
                st.write("**Model Used:** TCN Temporal Conv Net")

def process_image(file_path):
    with st.spinner("Analyzing Image..."):
        cls, conf = safe_predict_image(file_path)
        
        if cls == "Undetected":
            st.error("❌ FAILED SAFETY CHECK: No human content detected.")
        else:
            if conf >= 0.60:
                st.success("✅ Valid Analysis Complete")
                st.metric("Predicted Behavior", cls, f"{conf:.2%} Confidence")
            else:
                st.warning("⚠️ Low Confidence")
                st.metric("Behavior", cls, f"{conf:.2%} Confidence")


uploaded_file = st.sidebar.file_uploader("Upload File", type=['mp4', 'avi', 'mov'] if upload_type == "Video" else ['jpg', 'png', 'jpeg'])

if uploaded_file is not None:
    # Save the file to tempoary space for OpenCV
    tfile = tempfile.NamedTemporaryFile(delete=False) 
    tfile.write(uploaded_file.read())
    file_path = tfile.name
    
    st.markdown("### 👁️ Analysis Module")
    if upload_type == "Image":
        st.image(file_path, width=400)
    else:
        st.video(file_path)

    if st.button("🚀 START SCREENING"):
        if upload_type == "Video":
            process_video(file_path)
        else:
            process_image(file_path)
else:
    st.info("Please upload a file on the left sidebar to begin.")
