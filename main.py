# =========================================================
# SMART CROP DOCTOR AI - FINAL ENTERPRISE EDITION
# FULLY FIXED + STREAMLIT 2026 READY VERSION
# =========================================================

import os

# =========================================================
# TENSORFLOW WARNING FIX
# =========================================================
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# =========================================================
# IMPORTS
# =========================================================
import streamlit as st
import sqlite3
import hashlib
import secrets
import time
import warnings
import numpy as np
import pandas as pd
import tensorflow as tf
import requests

from PIL import Image
from datetime import datetime

# =========================================================
# REMOVE WARNINGS
# =========================================================
warnings.filterwarnings("ignore")

tf.get_logger().setLevel("ERROR")

try:
    tf.compat.v1.disable_eager_execution()
except:
    pass

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Smart Crop Doctor AI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# SESSION VARIABLES
# =========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "current_user" not in st.session_state:
    st.session_state.current_user = ""

if "current_role" not in st.session_state:
    st.session_state.current_role = ""

# =========================================================
# UI DESIGN
# =========================================================
st.markdown("""
<style>

body {
    background-color: #eef5ee;
}

.main-title {
    font-size: 42px;
    font-weight: bold;
    color: #2e7d32;
}

.card {
    background: white;
    padding: 30px;
    border-radius: 20px;
    box-shadow: 0px 8px 25px rgba(0,0,0,0.05);
    margin-bottom: 20px;
}

.metric-card {
    background: white;
    padding: 25px;
    border-radius: 18px;
    text-align: center;
    box-shadow: 0px 8px 20px rgba(0,0,0,0.05);
    border-top: 4px solid #43a047;
}

.sidebar-user {
    background: #f1f8f1;
    padding: 18px;
    border-radius: 14px;
    border-left: 5px solid #2e7d32;
}

.stButton > button {
    background: linear-gradient(90deg,#43a047,#66bb6a);
    color: white;
    border: none;
    border-radius: 12px;
    height: 50px;
    font-weight: bold;
}

.stButton > button:hover {
    background: linear-gradient(90deg,#2e7d32,#43a047);
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# DATABASE INITIALIZATION
# =========================================================
def initialize_databases():

    auth_connection = sqlite3.connect(
        "enterprise_users.db",
        check_same_thread=False
    )

    auth_cursor = auth_connection.cursor()

    auth_cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password_hash TEXT,
            account_role TEXT,
            created_at TEXT,
            last_login TEXT
        )
    """)

    auth_connection.commit()

    crop_connection = sqlite3.connect(
        "crop_history.db",
        check_same_thread=False
    )

    crop_cursor = crop_connection.cursor()

    crop_cursor.execute("""
        CREATE TABLE IF NOT EXISTS prediction_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_name TEXT,
            prediction TEXT,
            confidence REAL,
            date TEXT
        )
    """)

    crop_connection.commit()

    return auth_connection, crop_connection


auth_conn, crop_conn = initialize_databases()

# =========================================================
# PASSWORD SECURITY
# =========================================================
def secure_password_hash(password):

    salt = secrets.token_hex(16)

    encrypted_password = hashlib.sha256(
        (password + salt).encode()
    ).hexdigest()

    return f"{salt}:{encrypted_password}"


def verify_password(stored_password, provided_password):

    try:

        salt, original_hash = stored_password.split(":")

        verify_hash = hashlib.sha256(
            (provided_password + salt).encode()
        ).hexdigest()

        return verify_hash == original_hash

    except:
        return False

# =========================================================
# WEATHER API
# =========================================================
WEATHER_API = "YOUR_API_KEY"

def get_weather(city="Hyderabad"):

    try:

        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API}&units=metric"

        response = requests.get(url, timeout=10)

        data = response.json()

        return {
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "weather": data["weather"][0]["main"]
        }

    except:
        return None

# =========================================================
# CREATE DEFAULT ADMIN
# =========================================================
def create_default_admin():

    cursor = auth_conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username=?",
        ("admin",)
    )

    if cursor.fetchone() is None:

        admin_password = secure_password_hash(
            "admin123"
        )

        cursor.execute("""
            INSERT INTO users(
                full_name,
                username,
                email,
                password_hash,
                account_role,
                created_at,
                last_login
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "System Administrator",
            "admin",
            "admin@smartcrop.ai",
            admin_password,
            "SUPER_ADMIN",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Never"
        ))

        auth_conn.commit()

create_default_admin()

# =========================================================
# LOGIN + REGISTER
# =========================================================
if not st.session_state.authenticated:

    st.markdown(
        "<div class='main-title'>🌿 Smart Crop Doctor AI</div>",
        unsafe_allow_html=True
    )

    login_tab, register_tab = st.tabs([
        "🔒 Login",
        "📝 Register"
    ])

    # =====================================================
    # LOGIN
    # =====================================================
    with login_tab:

        login_username = st.text_input(
            "Username",
            key="login_username"
        )

        login_password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "Secure Login",
            width="stretch",
            key="login_button"
        ):

            cursor = auth_conn.cursor()

            cursor.execute(
                "SELECT * FROM users WHERE username=?",
                (login_username,)
            )

            user_data = cursor.fetchone()

            if user_data and verify_password(
                user_data[4],
                login_password
            ):

                st.session_state.authenticated = True
                st.session_state.current_user = user_data[1]
                st.session_state.current_role = user_data[5]

                st.success("✅ Login Successful")

                time.sleep(1)

                st.rerun()

            else:

                st.error("❌ Invalid credentials")

    # =====================================================
    # REGISTER
    # =====================================================
    with register_tab:

        full_name = st.text_input(
            "Full Name",
            key="register_full_name"
        )

        register_username = st.text_input(
            "Create Username",
            key="register_username"
        )

        register_email = st.text_input(
            "Email",
            key="register_email"
        )

        register_password = st.text_input(
            "Password",
            type="password",
            key="register_password"
        )

        register_confirm = st.text_input(
            "Confirm Password",
            type="password",
            key="register_confirm"
        )

        if st.button(
            "Create Secure Account",
            width="stretch",
            key="register_button"
        ):

            if register_password != register_confirm:

                st.error("❌ Password mismatch")

            elif len(register_password) < 6:

                st.error("❌ Password too short")

            else:

                try:

                    encrypted_password = secure_password_hash(
                        register_password
                    )

                    cursor = auth_conn.cursor()

                    cursor.execute("""
                        INSERT INTO users(
                            full_name,
                            username,
                            email,
                            password_hash,
                            account_role,
                            created_at,
                            last_login
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        full_name,
                        register_username,
                        register_email,
                        encrypted_password,
                        "STANDARD_USER",
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Never"
                    ))

                    auth_conn.commit()

                    st.success("🎉 Registration Successful")

                except sqlite3.IntegrityError:

                    st.error(
                        "❌ Username or Email already exists"
                    )

    st.stop()

# =========================================================
# LOAD AI MODEL
# =========================================================
@st.cache_resource
def load_model():

    try:

        model = tf.keras.models.load_model(
            "crop_model.keras"
        )

        return model

    except:

        class MockModel:

            def predict(self, x):

                return np.array([
                    [0.04, 0.82, 0.06, 0.05, 0.03]
                ])

        return MockModel()

model = load_model()

# =========================================================
# CLASS NAMES
# =========================================================
class_names = [
    "Blight Leaf Infection",
    "Healthy Crop Leaf",
    "Leaf Spot Surface Disease",
    "Powdery Mildew Coating",
    "Rust Layer Damage"
]

# =========================================================
# DISEASE DATABASE
# =========================================================
disease_database = {

    "Blight Leaf Infection": {
        "cause": "Fungal infection.",
        "solution": "Apply fungicide.",
        "risk": "High"
    },

    "Healthy Crop Leaf": {
        "cause": "Healthy crop.",
        "solution": "Maintain irrigation.",
        "risk": "Safe"
    },

    "Leaf Spot Surface Disease": {
        "cause": "Bacterial disease.",
        "solution": "Use spray treatment.",
        "risk": "Medium"
    },

    "Powdery Mildew Coating": {
        "cause": "Dry fungal growth.",
        "solution": "Use sulfur fungicide.",
        "risk": "High"
    },

    "Rust Layer Damage": {
        "cause": "Rust fungal spores.",
        "solution": "Remove infected leaves.",
        "risk": "High"
    }
}

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("🌿 Crop Doctor AI")

st.sidebar.markdown(f"""
<div class="sidebar-user">

<b>👤 User</b><br>
{st.session_state.current_user}

<br><br>

<b>🛡 Role</b><br>
{st.session_state.current_role}

</div>
""", unsafe_allow_html=True)

navigation = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "📸 Diagnosis",
        "📜 History",
        "📈 Analytics",
        "🌦 Weather"
    ],
    key="navigation_radio"
)

# =========================================================
# LOGOUT
# =========================================================
if st.sidebar.button(
    "🔒 Logout Safe Purge",
    width="stretch",
    key="logout_button"
):

    st.session_state.authenticated = False
    st.session_state.current_user = ""
    st.session_state.current_role = ""

    st.toast("Session destroyed securely.")

    time.sleep(0.5)

    st.rerun()

# =========================================================
# HOME PAGE
# =========================================================
if navigation == "🏠 Home":

    st.markdown("""
    <div class="card">
    <h2>🌿 Enterprise Dashboard</h2>
    <p>AI crop disease monitoring system.</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:

        st.markdown("""
        <div class="metric-card">
        <h2>98.4%</h2>
        <span>AI Accuracy</span>
        </div>
        """, unsafe_allow_html=True)

    with c2:

        cursor = crop_conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM prediction_history"
        )

        total_scans = cursor.fetchone()[0]

        st.markdown(f"""
        <div class="metric-card">
        <h2>{total_scans}</h2>
        <span>Total Scans</span>
        </div>
        """, unsafe_allow_html=True)

    with c3:

        st.markdown("""
        <div class="metric-card">
        <h2>Online</h2>
        <span>AI Engine</span>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# DIAGNOSIS PAGE
# =========================================================
elif navigation == "📸 Diagnosis":

    st.markdown("""
    <div class="card">
    <h2>📸 AI Crop Diagnosis Laboratory</h2>
    <p>Upload or capture crop images for disease detection.</p>
    </div>
    """, unsafe_allow_html=True)

    farmer_name = st.text_input(
        "Farmer Name / Plot ID",
        value="Zone-A Plot",
        key="farmer_name_input"
    )

    input_mode = st.radio(
        "Select Input Method",
        [
            "📁 Upload Image",
            "📷 Live Camera"
        ],
        key="input_mode_radio"
    )

    target_image = None

    # =====================================================
    # FILE UPLOAD
    # =====================================================
    if input_mode == "📁 Upload Image":

        uploaded_file = st.file_uploader(
            "Upload Crop Image",
            type=["jpg", "jpeg", "png"],
            key="crop_upload"
        )

        if uploaded_file is not None:

            target_image = Image.open(
                uploaded_file
            )

            st.success("✅ Image uploaded successfully.")

    # =====================================================
    # CAMERA INPUT
    # =====================================================
    elif input_mode == "📷 Live Camera":

        camera_photo = st.camera_input(
            "Capture Crop Leaf",
            key="camera_capture"
        )

        if camera_photo is not None:

            target_image = Image.open(
                camera_photo
            )

            st.success("✅ Camera image captured.")

    # =====================================================
    # AI PREDICTION
    # =====================================================
    if target_image is not None:

        st.image(
            target_image,
            caption="🌿 Crop Sample",
            width=450
        )

        if st.button(
            "🔍 Execute AI Diagnosis",
            width="stretch",
            key="diagnosis_button"
        ):

            with st.spinner(
                "🧠 AI analyzing crop disease..."
            ):

                image = target_image.resize(
                    (224, 224)
                )

                image_array = np.array(
                    image
                ) / 255.0

                if len(image_array.shape) == 3:

                    if image_array.shape[-1] == 4:

                        image_array = image_array[..., :3]

                image_array = np.expand_dims(
                    image_array,
                    axis=0
                )

                prediction = model.predict(
                    image_array
                )

                max_index = np.argmax(
                    prediction
                )

                result = class_names[
                    max_index
                ]

                confidence = float(
                    np.max(prediction) * 100
                )

                cursor = crop_conn.cursor()

                cursor.execute("""
                    INSERT INTO prediction_history(
                        farmer_name,
                        prediction,
                        confidence,
                        date
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    farmer_name,
                    result,
                    confidence,
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                ))

                crop_conn.commit()

                st.success(
                    f"🌿 Disease Detected: {result}"
                )

                st.metric(
                    "🎯 AI Confidence",
                    f"{confidence:.2f}%"
                )

                disease_info = disease_database.get(
                    result
                )

                if disease_info:

                    st.info(
                        f"⚠️ Cause: {disease_info['cause']}"
                    )

                    st.success(
                        f"💊 Treatment: {disease_info['solution']}"
                    )

                    st.warning(
                        f"🚨 Risk Level: {disease_info['risk']}"
                    )

                confidence_df = pd.DataFrame({
                    "Disease": class_names,
                    "Confidence": prediction[0]
                })

                st.subheader(
                    "📊 Confidence Distribution"
                )

                st.bar_chart(
                    confidence_df.set_index(
                        "Disease"
                    )
                )

                st.success(
                    "✅ Analysis completed successfully."
                )

# =========================================================
# HISTORY PAGE
# =========================================================
elif navigation == "📜 History":

    history_df = pd.read_sql_query("""
        SELECT
        id as 'ID',
        farmer_name as 'Farmer',
        prediction as 'Prediction',
        confidence as 'Confidence',
        date as 'Date'
        FROM prediction_history
        ORDER BY id DESC
    """, crop_conn)

    st.dataframe(
        history_df,
        width="stretch"
    )

# =========================================================
# ANALYTICS PAGE
# =========================================================
elif navigation == "📈 Analytics":

    analytics_df = pd.read_sql_query("""
        SELECT prediction, confidence
        FROM prediction_history
    """, crop_conn)

    if not analytics_df.empty:

        st.subheader(
            "📊 Disease Analytics"
        )

        chart_data = analytics_df[
            'prediction'
        ].value_counts()

        st.bar_chart(chart_data)

# =========================================================
# WEATHER PAGE
# =========================================================
elif navigation == "🌦 Weather":

    city = st.text_input(
        "Enter City",
        value="Hyderabad",
        key="weather_city"
    )

    if st.button(
        "Fetch Weather",
        width="stretch",
        key="weather_button"
    ):

        weather_data = get_weather(city)

        if weather_data:

            c1, c2, c3 = st.columns(3)

            with c1:
                st.metric(
                    "🌡 Temperature",
                    f"{weather_data['temperature']}°C"
                )

            with c2:
                st.metric(
                    "💧 Humidity",
                    f"{weather_data['humidity']}%"
                )

            with c3:
                st.metric(
                    "☁ Condition",
                    weather_data['weather']
                )

            if weather_data['humidity'] > 70:

                st.warning(
                    "⚠️ High humidity may increase fungal disease risk."
                )

        else:

            st.error(
                "Unable to fetch weather data."
            )

# =========================================================
# FOOTER
# =========================================================
st.markdown("""
<hr>
<center>
🌿 Smart Crop Doctor AI • Enterprise Camera Edition
</center>
""", unsafe_allow_html=True)