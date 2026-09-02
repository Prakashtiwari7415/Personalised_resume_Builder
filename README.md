# 🚀 AI Resume Optimizer & Job Matcher

An AI-powered web application built with **CrewAI**, **LiteLLM**, **Groq (Llama-3.3-70b)**, and **Gradio** that analyzes your resume (PDF/DOCX), generates detailed feedback, rewrites your resume into recruiter-ready Markdown, and finds matching job opportunities.

---

## 🛠️ Features

1. **📄 Multi-Format Resume Extraction**: Supports `.pdf`, `.docx`, and `.txt` resume files.
2. **📊 AI Resume Feedback**: Evaluates section structure, experience clarity, skill highlights, and provides a score out of 10.
3. **📝 AI Resume Rewrite**: Uses an executive resume writer agent to generate an optimized, high-impact Markdown resume.
4. **🎯 Job Matching**: Recommends targeted roles and live job opportunities based on location and skills.
5. **🔑 Flexible Key Configuration**: Enter API keys directly in the web interface or configure via `.env` file.

---

## ⚙️ Quick Start

### 1. Activate Virtual Environment & Install Dependencies

For Bash / Zsh:
```bash
source .venv/bin/activate
```

For Fish Shell:
```fish
source .venv/bin/activate.fish
```


### 2. Set Up API Keys

Copy or edit `.env` in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
SERPER_API_KEY=your_serper_api_key_here  # Optional for live Google search
```

* **GROQ API Key**: Get a free key at [console.groq.com](https://console.groq.com)
* **Serper API Key**: Get a free key at [serper.dev](https://serper.dev) (optional)

*Note: You can also enter API keys directly in the web UI settings tab.*

---

## 🚀 Running the Web App

Run the Gradio app:

```bash
python app.py
```

Open your browser and navigate to:
`http://localhost:7860`
# Personalised_resume_Builder
