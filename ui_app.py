
import streamlit as st
import requests
import json
import os

API_URL = "http://localhost:8000/recommend_job_description/"
RELOAD_URL = "http://localhost:8000/reload_data/"

st.title("🔍 Job Description Recommender & Editor")

position = st.text_input("Enter a position (e.g., ML Trainee, Backend Developer, etc.):")

recommendations = []
if position:
    response = requests.post(API_URL, json={"position_name": position})
    if response.status_code == 200:
        recommendations = response.json().get("recommendations", [])
    else:
        st.error("Error fetching recommendations from backend.")

selected_jd = ""
if recommendations:
    dropdown_options = [f"{rec['title']} - {rec['jd'][:60]}..." for rec in recommendations]
    selected = st.selectbox("Select a recommended JD:", dropdown_options)

    if selected:
        selected_index = dropdown_options.index(selected)
        selected_jd = recommendations[selected_index]["jd"]

edited_jd = st.text_area("✏️ Edit the Job Description:", value=selected_jd, height=200)

if st.button("Submit"):
    if position and edited_jd:
        new_entry = {
            "title": position.strip(),
            "jd": edited_jd.strip()
        }

        jds_data = []
        if os.path.exists("jds.json"):
            with open("jds.json", "r") as f:
                try:
                    jds_data = json.load(f)
                except json.JSONDecodeError:
                    jds_data = []

        jds_data = [entry for entry in jds_data if entry["title"].lower() != new_entry["title"].lower()]
        jds_data.append(new_entry)

        with open("jds.json", "w") as f:
            json.dump(jds_data, f, indent=2)

        st.success(f"✅ JD for '{position}' has been saved/updated in jds.json.")

        # Optional: Trigger backend refresh immediately
        with st.spinner("Rebuilding embeddings in ChromaDB..."):
            response = requests.post(RELOAD_URL)
            if response.status_code == 200:
                st.success("✅ ChromaDB updated with new data.")
            else:
                st.warning("⚠️ JD saved but ChromaDB update failed. Try '🔄 Refresh All'.")

st.markdown("---")
if st.button("🔄 Refresh All"):
    with st.spinner("Refreshing data in ChromaDB..."):
        response = requests.post(RELOAD_URL)
        if response.status_code == 200:
            result = response.json()
            st.success(f"✅ {result['message']}")
        else:
            st.error("❌ Failed to refresh backend. Check FastAPI server.")
