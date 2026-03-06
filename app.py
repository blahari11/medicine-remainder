import streamlit as st
import sqlite3
import hashlib
import requests
import schedule
import time
import threading
from plyer import notification

# -----------------------------
# DATABASE
# -----------------------------

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
email TEXT PRIMARY KEY,
password TEXT
)
""")
conn.commit()

# -----------------------------
# PASSWORD HASH
# -----------------------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# -----------------------------
# SIGNUP FUNCTION
# -----------------------------

def signup_user(email, password):
    try:
        cursor.execute(
            "INSERT INTO users VALUES (?,?)",
            (email, hash_password(password))
        )
        conn.commit()
        return True
    except:
        return False

# -----------------------------
# LOGIN FUNCTION
# -----------------------------

def login_user(email, password):

    cursor.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, hash_password(password))
    )

    data = cursor.fetchone()

    return data

# -----------------------------
# RESET PASSWORD
# -----------------------------

def reset_password(email, new_password):

    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cursor.fetchone()

    if user:
        cursor.execute(
            "UPDATE users SET password=? WHERE email=?",
            (hash_password(new_password), email)
        )
        conn.commit()
        return True
    else:
        return False

# -----------------------------
# AI FUNCTION
# -----------------------------

OPENROUTER_API_KEY = "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"

def ask_ai(medicine):

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "Medicine Reminder"
    }

    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {
                "role": "user",
                "content": f"Explain the medicine {medicine}, its uses, dosage, and precautions in simple words."
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    result = response.json()

    if "choices" not in result:
        return f"API Error: {result}"

    return result["choices"][0]["message"]["content"]

# -----------------------------
# NOTIFICATION
# -----------------------------

def send_notification(medicine):

    notification.notify(
        title="Medicine Reminder",
        message=f"Time to take your medicine: {medicine}",
        timeout=10
    )

def run_scheduler():

    while True:
        schedule.run_pending()
        time.sleep(1)

thread = threading.Thread(target=run_scheduler)
thread.daemon = True
thread.start()

# -----------------------------
# SESSION STATE
# -----------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# -----------------------------
# LOGIN / SIGNUP PAGE
# -----------------------------

if st.session_state.logged_in == False:

    st.title("💊 AI Medicine Reminder System")

    menu = ["Login", "Signup", "Forgot Password"]
    choice = st.sidebar.selectbox("Menu", menu)

    # ---------------- LOGIN ----------------
    if choice == "Login":

        st.subheader("Login Section")

        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):

            user = login_user(email, password)

            if user:

                st.session_state.logged_in = True
                st.session_state.email = email

                st.success("Login successful")
                st.rerun()

            else:
                st.error("Invalid email or password")

    # ---------------- SIGNUP ----------------
    elif choice == "Signup":

        st.subheader("Create New Account")

        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Create Account"):

            if signup_user(email, password):

                st.success("Account created successfully")

            else:
                st.error("User already exists")

    # ---------------- FORGOT PASSWORD ----------------
    elif choice == "Forgot Password":

        st.subheader("Reset Your Password")

        email = st.text_input("Enter your registered email")
        new_password = st.text_input("Enter new password", type="password")

        if st.button("Reset Password"):

            success = reset_password(email, new_password)

            if success:
                st.success("Password updated successfully. Please login.")

            else:
                st.error("Email not found")

# -----------------------------
# DASHBOARD
# -----------------------------

if st.session_state.logged_in:

    st.sidebar.write(f"Logged in as {st.session_state.email}")

    if st.sidebar.button("Logout"):

        st.session_state.logged_in = False
        st.rerun()

    st.title("💊 Medicine Reminder Dashboard")

    medicine = st.text_input("Enter Medicine Name")

    reminder_time = st.text_input(
        "Enter Reminder Time (HH:MM)",
        placeholder="Example: 14:35"
    )

    if st.button("Set Reminder"):

        schedule.every().day.at(reminder_time).do(
            send_notification, medicine
        )

        st.success(f"Reminder set for {medicine} at {reminder_time}")

    st.subheader("AI Medicine Explanation")

    if st.button("Explain Medicine"):

        if medicine == "":
            st.warning("Enter medicine name")

        else:
            with st.spinner("AI is analyzing medicine..."):
                explanation = ask_ai(medicine)

            st.write(explanation)