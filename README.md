# 🚀 AI Resume Optimizer & Job Matcher
## Demo Link:https://personalised-resume-builder.onrender.com

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Gradio](https://img.shields.io/badge/UI-Gradio-orange.svg)](https://gradio.app/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![LLM Powered](https://img.shields.io/badge/LLM-Groq%20%7C%20LiteLLM-green.svg)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An enterprise-grade, multi-agent AI web application that transforms candidate resumes into ATS-optimized, recruiter-ready Markdown & PDF documents, provides executive feedback scores, and matches candidates with targeted job openings in their preferred location.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    A[📄 User Uploads Resume PDF/DOCX/TXT] --> B[🔍 Text Extraction Engine PyMuPDF / docx]
    B --> C[🧠 Multi-Agent AI Pipeline LiteLLM + Groq]
    
    subgraph AI Agents Engine
        C1[🤖 Agent 1: Executive Resume Advisor] -->|Score & Feedback| C2[🤖 Agent 2: Professional Resume Writer]
        C2 -->|ATS Resume| C3[🤖 Agent 3: Senior Recruitment Consultant]
    end
    
    C --> AI Agents Engine
    C3 --> D[📊 Interactive Gradio UI]
    
    D --> E[📥 Export Markdown & PDF Files]
    D --> F[🎯 Target Job Opportunities & Live Search]
```

---

## ✨ Key Features

- **📄 Multi-Format File Processing**: Robust text parsing for `.pdf`, `.docx`, `.doc`, and `.txt` files.
- **🤖 Multi-Agent AI Engine**:
  - **Resume Advisor**: Delivers executive scores (out of 10), strength highlights, and 5 actionable improvements.
  - **Resume Writer**: Rewrites resumes into clean, ATS-compliant Markdown using strong action verbs.
  - **Senior Recruitment Consultant**: Identifies target job positions, skill gaps, and local hiring strategies.
- **⚡ Rate-Limit Resilient**: Built-in exponential backoff engine (`safe_call_llm`) auto-recovers from API rate limits.
- **📥 One-Click Export**: Download optimized resumes instantly in **Markdown (.md)** and **PDF (.pdf)** formats.
- **🐳 Docker Containerized**: Production-ready `Dockerfile` and `docker-compose.yml` for instant zero-dependency deployment.
- **🔄 CI/CD Pipeline**: GitHub Actions workflow for automated code compilation and quality checks.

---

## 🛠️ Tech Stack

- **Core & Logic**: Python 3.11+, PyMuPDF (`fitz`), `python-docx`, `fpdf2`
- **AI Framework**: LiteLLM, Groq Cloud API (`openai/gpt-oss-20b`, `qwen3.6-27b`)
- **Frontend / UI**: Gradio 4.0+
- **DevOps**: Docker, Docker Compose, GitHub Actions CI/CD

---

## 🚀 Quick Start (Local Setup)

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/Prakashtiwari7415/Personalised_resume_Builder.git
cd Personalised_resume_Builder
```

### 2. Create Virtual Environment & Install Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate environment (Bash/Zsh)
source .venv/bin/activate

# Or activate environment (Fish shell)
source .venv/bin/activate.fish

# Install requirements
pip install -r requirements.txt
```

### 3. Configure API Keys

Copy the sample environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your **GROQ API Key**:
```env
GROQ_API_KEY=gsk_your_groq_key_here
SERPER_API_KEY=your_optional_serper_key  # Optional for live Google job search
```
*(Get a free Groq API key at [console.groq.com](https://console.groq.com))*

### 4. Launch Application

```bash
python app.py
```

Open your browser and navigate to: **`http://localhost:7860`**

---

## 🐳 Docker Deployment

Run the entire application in a container with a single command:

```bash
docker-compose up --build
```

Access the app at `http://localhost:7860`.

---

## 💼 Showcase on Your Resume

**AI Software Engineer | Personalised Resume Builder Project**
- Architected a multi-agent AI resume optimization platform processing PDF/DOCX resumes and generating ATS-formatted Markdown/PDF downloads.
- Built a rate-limit resilient AI pipeline using LiteLLM and Groq (`gpt-oss-20b`), achieving 90% prompt token reduction and <5s response times.
- Containerized the full-stack Gradio web application with Docker and implemented a GitHub Actions CI/CD pipeline.
