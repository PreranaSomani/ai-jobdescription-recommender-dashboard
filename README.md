
# AI-Powered Job Description Recommender & Editor

A smart dashboard to recommend, edit, and manage job descriptions (JDs) using semantic search and live backend updates.

## Project Overview

This project allows users to search for job positions, get AI-recommended job descriptions, edit them, and save those updates. All changes are automatically synced with a FastAPI backend powered by ChromaDB (a vector database).

## How It Works

Job descriptions are stored in a file called `jds.json`. Each entry contains a `title` and a `jd` (the description).

### Backend (FastAPI + ChromaDB)

- On startup, the backend reads job descriptions from `jds.json`, embeds them using the `all-mpnet-base-v2` model, and stores them in ChromaDB.
- Titles are repeated three times during embedding to make them more relevant in semantic search.
- API Endpoints:
  - `POST /recommend_job_description/`: Returns the top 3 matching JDs based on the entered position
  - `POST /reload_data/`: Reloads the `jds.json` file and refreshes ChromaDB

### Frontend (Streamlit)

- Users can enter a job title and receive AI-powered JD suggestions.
- Users can view, edit, and save the job description to `jds.json`.
- Once saved, the app automatically triggers the backend to reload and update the vector database.
- A manual "🔄 Refresh All" button is also available for force-refreshing the data.

## Features

- AI-based job description recommendations using semantic similarity
- Editable UI built with Streamlit
- Real-time backend synchronization with FastAPI
- Persistent and scalable vector search using ChromaDB

## Tech Stack

- Python
- FastAPI
- Streamlit
- ChromaDB
- SentenceTransformers (`all-mpnet-base-v2`)

## Run Locally

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
