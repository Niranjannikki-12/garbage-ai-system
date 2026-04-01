import streamlit as st
import joblib
import re
import pandas as pd

# 🌈 Page config
st.set_page_config(page_title="Garbage AI System", page_icon="♻️", layout="wide")

# 🌈 Custom CSS (colors + styling)
st.markdown("""
    <style>
    .main {
        background-color: #f5f7fa;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 10px;
        height: 3em;
        width: 100%;
    }
    .stTextInput>div>div>input {
        border-radius: 10px;
    }
    .stTextArea textarea {
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Load model
model = joblib.load("model/model.pkl")
vectorizer = joblib.load("model/vectorizer.pkl")

# Clean function
def clean(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z ]', '', text)
    return text

# 🌟 Title
st.title("♻️ AI Garbage Complaint System")
st.markdown("### Smart Waste Management & Grievance Redressal")

# Layout (2 columns)
col1, col2 = st.columns(2)

with col1:
    text = st.text_area("📝 Enter Complaint")

with col2:
    location = st.text_input("📍 Enter Location")

# Submit
if st.button("🚀 Submit Complaint"):
    cleaned = clean(text)
    vec = vectorizer.transform([cleaned])
    category = model.predict(vec)[0]

    st.success(f"✅ Category: {category}")

    # Department
    dept_map = {
        "Garbage Not Collected": "Sanitation Dept",
        "Overflowing Bins": "Waste Management",
        "Street Cleanliness": "Municipal Cleaning",
        "Illegal Dumping": "Inspection Team"
    }

    dept = dept_map.get(category, "General Dept")
    st.info(f"🏢 Department: {dept}")

    # Alerts
    if category == "Overflowing Bins":
        st.warning("⚠️ High Priority: Immediate cleanup needed!")
    elif category == "Illegal Dumping":
        st.error("🚨 Illegal activity detected!")

    # Priority
    high_priority_keywords = ["bad smell", "disease", "urgent", "overflow", "mosquito"]
    priority = "Normal"

    for word in high_priority_keywords:
        if word in text.lower():
            priority = "High"
            break

    if priority == "High":
        st.error("🚨 High Priority Complaint!")
    else:
        st.success("🟢 Normal Priority")

    # Save
    df = pd.read_csv("data/complaints.csv")
    new_data = pd.DataFrame([[text, location, category, "Pending"]],
                            columns=["complaint","location","category","status"])

    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv("data/complaints.csv", index=False)

    st.success("💾 Complaint saved!")

    st.rerun()

# 📊 Dashboard
st.markdown("---")
st.header("📊 Dashboard")

df = pd.read_csv("data/complaints.csv")

col1, col2, col3 = st.columns(3)

col1.metric("Total Complaints", len(df))
col2.metric("Pending", (df['status'] == "Pending").sum())
col3.metric("Resolved", (df['status'] == "Resolved").sum())

st.markdown("### 📌 Complaints by Category")
st.bar_chart(df['category'].value_counts())

st.markdown("### 📍 Complaints by Location")
st.bar_chart(df['location'].value_counts())

# 🔥 Hotspots
st.markdown("### 🔥 Top 3 Hotspots")
top_areas = df['location'].value_counts().head(3)
for area, count in top_areas.items():
    st.write(f"📍 {area} → {count}")

# 🧠 Insights
st.markdown("### 🧠 AI Insights")
st.success(f"Most common issue: {df['category'].value_counts().idxmax()}")
st.info(f"Most affected area: {df['location'].value_counts().idxmax()}")

# 🔄 Status Update
st.markdown("### 🔄 Update Status")

st.dataframe(df)

index = st.number_input("Enter Index", min_value=0, step=1)

if st.button("✅ Mark as Resolved"):
    df.loc[index, 'status'] = "Resolved"
    df.to_csv("data/complaints.csv", index=False)
    st.success("Updated successfully!")