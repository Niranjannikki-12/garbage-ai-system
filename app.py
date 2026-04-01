import streamlit as st
import joblib
import re
import pandas as pd
import os
import plotly.express as px
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# -------------------------------
# 📁 File Setup
# -------------------------------
if not os.path.exists("data/complaints.csv"):
    df_init = pd.DataFrame(columns=["complaint","location","category","status","time"])
    df_init.to_csv("data/complaints.csv", index=False)

# -------------------------------
# 🔐 LOGIN SYSTEM
# -------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

st.sidebar.title("🔐 Login")
login_type = st.sidebar.selectbox("Login as", ["User", "Admin"])

admins = {
    "admin": "admin123",
    "Nikitha23": "Nikitha@23"
}

if login_type == "User":
    st.session_state.logged_in = True
    st.session_state.role = "User"

if login_type == "Admin":
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if username in admins and password == admins[username]:
            st.session_state.logged_in = True
            st.session_state.role = "Admin"
            st.sidebar.success("✅ Logged in")
        else:
            st.sidebar.error("❌ Invalid credentials")

if not st.session_state.logged_in:
    st.warning("🔒 Please login to continue")
    st.stop()

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.role = None
    st.rerun()

# -------------------------------
# 🤖 Load Model
# -------------------------------
model = joblib.load("model/model.pkl")
vectorizer = joblib.load("model/vectorizer.pkl")

def clean(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z ]', '', text)
    return text.strip()

# -------------------------------
# 🎨 UI
# -------------------------------
st.set_page_config(page_title="Smart Waste Management", layout="wide")
st.markdown("<h1 style='text-align:center;'>♻️ Smart Waste Management System</h1>", unsafe_allow_html=True)

# -------------------------------
# 📊 Load Data
# -------------------------------
df = pd.read_csv("data/complaints.csv")
df = df.drop_duplicates()

# -------------------------------
# 📑 Tabs
# -------------------------------
if st.session_state.role == "User":
    tab1 = st.tabs(["📝 Complaint"])[0]
else:
    tab1, tab2, tab3 = st.tabs(["📝 Complaint", "📊 Dashboard", "⚙️ Admin"])

# ===============================
# 📝 USER TAB
# ===============================
with tab1:
    if st.session_state.role != "User":
        st.warning("❌ Only Users can submit complaints")
    else:
        st.subheader("📝 Register Complaint")

        text = st.text_area("Enter Complaint")
        location = st.text_input("Enter Location")

        if st.button("Submit Complaint"):
            if not text.strip() or not location.strip():
                st.error("❌ Fill all fields")
                st.stop()

            cleaned = clean(text)
            vec = vectorizer.transform([cleaned])
            category = model.predict(vec)[0]

            st.success(f"Category: {category}")

            if any(k in text.lower() for k in ["bad smell","mosquito","overflow"]):
                st.error("🚨 High Priority Complaint!")

            new = pd.DataFrame([[text, location, category, "Pending",
                                 datetime.now().strftime("%Y-%m-%d %H:%M:%S")]],
                               columns=["complaint","location","category","status","time"])

            df = pd.concat([df, new], ignore_index=True)
            df.to_csv("data/complaints.csv", index=False)

            st.success("Complaint Submitted!")
            st.rerun()

# ===============================
# 📊 DASHBOARD
# ===============================
if st.session_state.role == "Admin":
    with tab2:
        st.subheader("📊 Dashboard")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total", len(df))
        col2.metric("Pending", (df['status']=="Pending").sum())
        col3.metric("Resolved", (df['status']=="Resolved").sum())

        st.subheader("🚨 Alerts")
        alerts = df[df['complaint'].str.contains("bad smell|mosquito|overflow", case=False)]
        for _, row in alerts.iterrows():
            st.error(f"{row['location']} → {row['complaint']}")

        st.plotly_chart(px.bar(df['category'].value_counts().reset_index(),
                               x='category', y='count'),
                        use_container_width=True)

        st.plotly_chart(px.bar(df['location'].value_counts().reset_index(),
                               x='location', y='count'),
                        use_container_width=True)

        st.plotly_chart(px.pie(df, names='category'), use_container_width=True)

        # Map
        st.subheader("🗺 Hotspot Map")

        location_map = {
            "Ameerpet":[17.4375,78.4483],
            "Madhapur":[17.4483,78.3915],
            "Miyapur":[17.4948,78.3915],
            "Kukatpally":[17.4849,78.4138],
            "Gachibowli":[17.4401,78.3489],
            "Hitech City":[17.4435,78.3772],
            "Banjara Hills":[17.4126,78.4482]
        }

        m = folium.Map(location=[17.45,78.40], zoom_start=11)
        cluster = MarkerCluster().add_to(m)

        counts = df['location'].value_counts()

        for area, count in counts.items():
            if area in location_map:
                lat, lon = location_map[area]
                color = "red" if count>=15 else "orange" if count>=8 else "green"

                folium.Marker(
                    [lat,lon],
                    popup=f"{area} ({count})",
                    tooltip=area,
                    icon=folium.Icon(color=color)
                ).add_to(cluster)

        st_folium(m, width=900, height=500)

# ===============================
# ⚙️ ADMIN PANEL
# ===============================
if st.session_state.role == "Admin":
    with tab3:
        st.subheader("⚙️ Manage Complaints")

        col1, col2 = st.columns(2)
        loc_filter = col1.selectbox("Location", ["All"] + list(df['location'].unique()))
        status_filter = col2.selectbox("Status", ["All","Pending","Resolved"])

        filtered_df = df.copy()

        if loc_filter != "All":
            filtered_df = filtered_df[filtered_df['location'] == loc_filter]

        if status_filter != "All":
            filtered_df = filtered_df[filtered_df['status'] == status_filter]

        # ✅ SAFE TABLE (FIXED)
        st.dataframe(filtered_df)

        # Search
        search = st.text_input("Search complaint")
        if search:
            st.dataframe(filtered_df[filtered_df['complaint'].str.contains(search, case=False)])

        # Update
        if len(filtered_df) > 0:
            idx = st.selectbox("Select Index", filtered_df.index)

            if st.button("Mark as Resolved"):
                df.loc[idx,'status'] = "Resolved"
                df.to_csv("data/complaints.csv", index=False)
                st.success("Updated!")
                st.rerun()