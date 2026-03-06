import streamlit as st
import sqlite3
import hashlib
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# -----------------------------
# AUTO REFRESH (for reminders)
# -----------------------------

st_autorefresh(interval=30000, key="refresh")  # refresh every 30 seconds

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
# SIGNUP
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
# LOGIN
# -----------------------------

def login_user(email, password):

    cursor.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, hash_password(password))
    )

    return cursor.fetchone()


# -----------------------------
# RESET PASSWORD
# -----------------------------

def reset_password(email, new_password):

    cursor.execute(
        "SELECT * FROM users WHERE email=?",
        (email,)
    )

    user = cursor.fetchone()

    if user:

        cursor.execute(
            "UPDATE users SET password=? WHERE email=?",
            (hash_password(new_password), email)
        )

        conn.commit()
        return True

    return False


# -----------------------------
# AI MEDICINE EXPLANATION
# -----------------------------

OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]

def ask_ai(medicine):

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {
                "role": "user",
                "content": f"Explain the medicine {medicine}, its uses, dosage and precautions in simple simple words."
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    result = response.json()

    if "choices" not in result:
        return f"API Error: {result}"

    return result["choices"][0]["message"]["content"]


# -----------------------------
# SESSION STATE
# -----------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


# -----------------------------
# LOGIN / SIGNUP PAGE
# -----------------------------

if not st.session_state.logged_in:

    st.title("💊 AI Medicine Reminder System")

    menu = ["Login", "Signup", "Forgot Password"]

    choice = st.sidebar.selectbox("Menu", menu)

    email = st.text_input("Email")

    if choice == "Login":

        password = st.text_input("Password", type="password")

        if st.button("Login"):

            user = login_user(email, password)

            if user:

                st.session_state.logged_in = True
                st.session_state.email = email

                st.success("Login Successful")

                st.rerun()

            else:

                st.error("Invalid email or password")


    elif choice == "Signup":

        password = st.text_input("Create Password", type="password")

        if st.button("Create Account"):

            if signup_user(email, password):

                st.success("Account created successfully")

            else:

                st.error("User already exists")


    elif choice == "Forgot Password":

        new_password = st.text_input("Enter New Password", type="password")

        if st.button("Reset Password"):

            success = reset_password(email, new_password)

            if success:

                st.success("Password updated successfully")

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
        placeholder="Example: 14:30"
    )


    if st.button("Set Reminder"):

        st.session_state.reminder_time = reminder_time
        st.session_state.medicine = medicine

        st.success(f"Reminder set for {medicine} at {reminder_time}")


    # -----------------------------
    # CHECK REMINDER
    # -----------------------------

    if "reminder_time" in st.session_state:

        current_time = datetime.now().strftime("%H:%M")

        if current_time == st.session_state.reminder_time:

            st.warning(f"💊 Time to take your medicine: {st.session_state.medicine}")


    # -----------------------------
    # AI MEDICINE EXPLANATION
    # -----------------------------

    st.subheader("AI Medicine Explanation")

    if st.button("Explain Medicine"):

        if medicine == "":

            st.warning("Please enter medicine name")

        else:

            with st.spinner("AI analyzing medicine..."):

                explanation = ask_ai(medicine)

            st.write(explanation)