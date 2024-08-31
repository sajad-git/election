import streamlit as st
import pandas as pd
import os
import re
import base64
import json
import zipfile
import io

# File paths
config_path = "config.json"
votes_folder = "votes"

# Ensure votes folder exists
if not os.path.exists(votes_folder):
    os.makedirs(votes_folder)

# Load or create config
def load_or_create_config():
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    else:
        default_config = {
            "candidates": ["امیرعلی نیکو مقدم","طاها یزدانیان", "محمدمهدی لطفی"],
            "current_file": "votes_log_semnan.xlsx",
            "is_active": True,
            "admin_password": "admin123"  # Default password, should be changed
        }
        with open(config_path, 'w') as f:
            json.dump(default_config, f)
        return default_config

# Save config
def save_config(config):
    with open(config_path, 'w') as f:
        json.dump(config, f)

# Load config
config = load_or_create_config()

# Function to load or create the Excel file
def load_or_create_excel(file_name):
    file_path = os.path.join(votes_folder, file_name)
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=['کد ملی', 'نام', 'نام خانوادگی', 'رای داده شده به'])
        df.to_excel(file_path, index=False)
        return df
    return pd.read_excel(file_path)

# Load the existing votes
df = load_or_create_excel(config['current_file'])

# Function to load and encode the background image
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Function to set the background image
def set_background(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = '''
    <style>
    .stApp {
        background-image: url("data:image/png;base64,%s");
        background-size: cover;
    }
    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)

# Set the background image (replace 'background.png' with your image file name)
set_background('background.png')

# Custom CSS for Persian font and RTL
st.markdown("""
<style>
button {
    height: auto;
    padding-top: 10px !important;
    padding-bottom: 10px !important;
}

@font-face {
    font-family: 'Vazir';
    src: url('https://cdn.jsdelivr.net/gh/rastikerdar/vazir-font@v30.1.0/dist/Vazir-Regular.woff2') format('woff2');
    font-weight: normal;
    font-style: normal;
}

body {
    font-family: 'Vazir', sans-serif !important;
    direction: rtl;
}

.stTextInput > div > div > input,
.stSelectbox > div > div > div,
.stButton > button,
.css-1y4p8pa,
.stMarkdown,
h1, h2, h3, p, span {
    font-family: 'Vazir', sans-serif !important;
    direction: rtl;
}

.main .block-container {
    direction: rtl;
    text-align: right;
    background-color: rgba(255, 255, 255, 0.8);
    padding: 2rem;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# Function to convert English numerals to Persian
def to_persian_numerals(text):
    persian_numerals = '۰۱۲۳۴۵۶۷۸۹'
    return ''.join(persian_numerals[int(c)] if c.isdigit() else c for c in str(text))

# Function to check if a National Code has already voted
def has_voted(national_code):
    return int(national_code) in df['کد ملی'].values.tolist()

# Function to validate the national code
def is_valid_national_code(code):
    return bool(re.match(r'^\d{10}$', code))

# Function to validate name (first name or last name)
def is_valid_name(name):
    return len(name.strip()) > 2

# Admin login
def admin_login():
    st.sidebar.title("ورود مدیر")
    password = st.sidebar.text_input("رمز عبور", type="password")
    return password == config['admin_password']

# Admin page
def admin_page():
    st.title("صفحه مدیریت")
    
    # Edit candidates
    st.header("ویرایش لیست نامزدها")
    new_candidates = []
    for i in range(5):
        candidate = st.text_input(f"نامزد {i+1}", value=config['candidates'][i] if i < len(config['candidates']) else "")
        if candidate:
            new_candidates.append(candidate)
    
    if st.button("بروزرسانی لیست نامزدها"):
        config['candidates'] = new_candidates
        save_config(config)
        st.success("لیست نامزدها بروزرسانی شد.")
    
    # Edit export file name
    st.header("ویرایش نام فایل خروجی")
    new_file_name = st.text_input("نام فایل جدید", value=config['current_file'])
    if st.button("تغییر نام فایل"):
        config['current_file'] = new_file_name
        save_config(config)
        st.success("نام فایل خروجی تغییر کرد.")
    
    # Activate/Deactivate election
    st.header("فعال/غیرفعال کردن انتخابات")
    is_active = st.checkbox("انتخابات فعال است", value=config['is_active'])
    if st.button("بروزرسانی وضعیت انتخابات"):
        config['is_active'] = is_active
        save_config(config)
        st.success("وضعیت انتخابات بروزرسانی شد.")
        
    st.header("دانلود فایل‌های رای‌گیری")
    excel_files = [f for f in os.listdir(votes_folder) if f.endswith('.xlsx')]
    
    if excel_files:
        selected_file = st.selectbox("انتخاب فایل برای دانلود:", excel_files)
        
        if st.button("دانلود فایل انتخاب شده"):
            file_path = os.path.join(votes_folder, selected_file)
            with open(file_path, "rb") as file:
                btn = st.download_button(
                    label="دانلود",
                    data=file,
                    file_name=selected_file,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    else:
        st.write("هیچ فایل Excel در پوشه رای‌گیری یافت نشد.")

    # Option to download all files as a zip
    if excel_files:
        if st.button("دانلود همه فایل‌ها به صورت فشرده"):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for file in excel_files:
                    file_path = os.path.join(votes_folder, file)
                    zip_file.write(file_path, file)
            
            zip_buffer.seek(0)
            st.download_button(
                label="دانلود فایل فشرده",
                data=zip_buffer,
                file_name="all_vote_files.zip",
                mime="application/zip"
            )

def voting_page():
    set_background('background.png')
    
    st.markdown("<h1 style='text-align: right; font-family: Vazir, sans-serif;'>انتخابات قرارگاه استانی ۱۴۰۳</h1>", unsafe_allow_html=True)
    
    if not config['is_active']:
        st.error("انتخابات در حال حاضر غیرفعال است.")
        return

    # Input fields for the voter
    national_code = st.text_input("کد ملی خود را وارد کنید (۱۰ رقم):", key="national_code")
    first_name = st.text_input("نام خود را وارد کنید (بیش از ۲ حرف):", key="first_name")
    last_name = st.text_input("نام خانوادگی خود را وارد کنید (بیش از ۲ حرف):", key="last_name")

    # Use the updated candidates list from config
    vote = st.selectbox("نامزد مورد نظر خود را انتخاب کنید:", config['candidates'])

    # Use session state to manage the voting process
    if 'vote_stage' not in st.session_state:
        st.session_state.vote_stage = 'initial'

    # Submit button
    if st.session_state.vote_stage == 'initial' and st.button("ثبت رای"):
        if national_code and first_name and last_name and vote:
            errors = []
            if not is_valid_national_code(national_code):
                errors.append("کد ملی نامعتبر است. لطفا یک عدد ۱۰ رقمی وارد کنید.")
            if not is_valid_name(first_name):
                errors.append("نام باید بیش از ۲ حرف باشد.")
            if not is_valid_name(last_name):
                errors.append("نام خانوادگی باید بیش از ۲ حرف باشد.")
            
            if errors:
                for error in errors:
                    st.markdown(f"<p style='color: red;'>{to_persian_numerals(error)}</p>", unsafe_allow_html=True)
            elif has_voted(national_code):
                st.markdown("<p style='color: red;'>شما قبلا رای داده‌اید. هر فرد تنها یک بار می‌تواند رای دهد.</p>", unsafe_allow_html=True)
            else:
                st.session_state.vote_stage = 'confirm'
        else:
            st.markdown("<p style='color: red;'>لطفا تمام فیلدها را پر کنید.</p>", unsafe_allow_html=True)

    # Confirmation step
    if st.session_state.vote_stage == 'confirm':
        st.markdown(f"<p style='color: orange;'>شما در حال رای دادن به {vote} هستید. آیا مطمئن هستید؟</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("تایید رای"):
                # Double-check to prevent race conditions
                if not has_voted(national_code):
                    # Log the vote
                    new_vote = pd.DataFrame({
                        'کد ملی': [int(national_code)],
                        'نام': [first_name],
                        'نام خانوادگی': [last_name],
                        'رای داده شده به': [vote]
                    })
                    global df
                    df = pd.concat([df, new_vote], ignore_index=True)
                    df.to_excel(os.path.join(votes_folder, config['current_file']), index=False)
                    st.markdown("<p style='color: green;'>از رای شما متشکریم!</p>", unsafe_allow_html=True)
                    st.session_state.vote_stage = 'voted'
                else:
                    st.markdown("<p style='color: red;'>شما قبلا رای داده‌اید. هر فرد تنها یک بار می‌تواند رای دهد.</p>", unsafe_allow_html=True)
                    st.session_state.vote_stage = 'initial'
        with col2:
            if st.button("لغو"):
                st.session_state.vote_stage = 'initial'

# Main app logic
def main():
    if admin_login():
        admin_page()
    else:
        voting_page()

if __name__ == "__main__":
    main()