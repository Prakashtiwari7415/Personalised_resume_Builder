# Warning control
import os
import re
import time
import warnings
warnings.filterwarnings('ignore')

from dotenv import load_dotenv
load_dotenv()

import fitz  # PyMuPDF for PDF processing
import docx  # python-docx for DOCX processing
import gradio as gr
import requests
import litellm

# Configure LiteLLM for retries and param dropping
litellm.drop_params = True

# Monkeypatch litellm.completion to remove Groq-unsupported cache fields
_original_completion = litellm.completion
def _clean_completion(*args, **kwargs):
    kwargs.pop('cache_prompt', None)
    if 'messages' in kwargs and isinstance(kwargs['messages'], list):
        for msg in kwargs['messages']:
            if isinstance(msg, dict):
                msg.pop('cache_breakpoint', None)
                msg.pop('cache_control', None)
    return _original_completion(*args, **kwargs)

litellm.completion = _clean_completion


def extract_text_from_resume(file_input):
    """Determines file type and extracts text cleanly."""
    if not file_input:
        return None, "No file provided."

    file_path = file_input.name if hasattr(file_input, 'name') else str(file_input)

    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == ".pdf":
            doc = fitz.open(file_path)
            text = "\n".join([page.get_text() for page in doc])
            return text.strip(), None
        elif ext in [".docx", ".doc"]:
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            return text.strip(), None
        elif ext in [".txt", ".md"]:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read().strip(), None
        else:
            return None, f"Unsupported file format '{ext}'. Please upload a PDF, DOCX, or TXT file."
    except Exception as e:
        return None, f"Failed to extract text from file: {str(e)}"


def clean_markdown_reasoning(text):
    """Strips internal LLM thinking tags if present in model output."""
    if not text:
        return ""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    return text


def safe_call_llm(model_name, api_key, system_prompt, user_prompt, max_retries=4):
    """
    Executes an LLM request with automatic RateLimit retry handling.
    If Groq returns a TPM/RPM rate limit, it waits the exact requested time and retries.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    llm_model = f"groq/{model_name}" if not model_name.startswith("groq/") else model_name

    for attempt in range(max_retries):
        try:
            res = litellm.completion(
                model=llm_model,
                api_key=api_key,
                messages=messages,
                temperature=0.3
            )
            raw_content = res.choices[0].message.content
            return clean_markdown_reasoning(raw_content)
        except litellm.RateLimitError as e:
            err_str = str(e)
            match = re.search(r'try again in (\d+\.?\d*)s', err_str)
            wait_time = float(match.group(1)) + 1.5 if match else 12.0
            if attempt < max_retries - 1:
                print(f"⏳ Rate limit reached on {model_name}. Auto-waiting {wait_time:.1f}s (Attempt {attempt+1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                raise Exception(f"Rate limit exceeded after {max_retries} attempts. Please try again in 30 seconds.")
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                raise e


def search_serper_jobs(query, location, serper_key):
    """Searches live job listings using Serper API if key is provided."""
    if not serper_key:
        return ""
    try:
        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": serper_key, "Content-Type": "application/json"}
        payload = {"q": f"{query} jobs in {location}"}
        res = requests.post(url, headers=headers, json=payload, timeout=8)
        if res.status_code == 200:
            results = res.json().get("organic", [])[:5]
            job_snippets = []
            for item in results:
                title = item.get("title", "Job Listing")
                snippet = item.get("snippet", "")
                link = item.get("link", "#")
                job_snippets.append(f"- **[{title}]({link})**: {snippet}")
            return "\n".join(job_snippets)
    except Exception:
        pass
    return ""


def resume_agent(file_obj, location, groq_key_input="", serper_key_input="", model_choice=""):
    """Main Multi-Agent Workflow for Resume Optimization and Job Matching."""
    groq_key = (groq_key_input or os.getenv("GROQ_API_KEY") or "").strip()
    serper_key = (serper_key_input or os.getenv("SERPER_API_KEY") or "").strip()

    if not groq_key:
        err_msg = (
            "### ⚠️ GROQ API Key Required\n\n"
            "Please enter your **GROQ API Key** in the **API Key Settings** section below, "
            "or configure `GROQ_API_KEY` in your `.env` file.\n\n"
            "👉 Get a free key at [console.groq.com](https://console.groq.com)"
        )
        return err_msg, err_msg, err_msg

    if not file_obj:
        err_msg = "### ⚠️ Missing File\n\nPlease upload a resume file in PDF or DOCX format."
        return err_msg, err_msg, err_msg

    resume_text, extract_error = extract_text_from_resume(file_obj)
    if extract_error:
        err_msg = f"### ⚠️ File Error\n\n{extract_error}"
        return err_msg, err_msg, err_msg

    if not resume_text or len(resume_text.strip()) < 20:
        err_msg = "### ⚠️ Empty Resume\n\nCould not extract readable text from the uploaded file."
        return err_msg, err_msg, err_msg

    target_location = location.strip() if location and location.strip() else "Remote / Flexible"
    selected_model = model_choice.strip() if model_choice else "openai/gpt-oss-20b"

    try:
        # Agent 1: Resume Advisor
        advisor_system = (
            "You are a veteran Executive Resume Advisor and Senior Recruiter. "
            "Evaluate resumes objectively, identifying strengths, formatting weaknesses, and impact gaps."
        )
        advisor_prompt = (
            f"Analyze the following resume for a candidate seeking roles in '{target_location}'.\n\n"
            f"Resume Text:\n{resume_text}\n\n"
            "Provide:\n"
            "1. **Overall Resume Score (out of 10)**\n"
            "2. **Strengths Overview**\n"
            "3. **4-5 Specific Actionable Improvements** (Quantifiable metrics, section headers, active verbs, skill additions)."
        )
        print("🤖 Running Agent 1: Resume Advisor...")
        feedback_output = safe_call_llm(selected_model, groq_key, advisor_system, advisor_prompt)
        time.sleep(1)

        # Agent 2: Resume Writer
        writer_system = (
            "You are an expert Resume Writer and Career Strategist. "
            "You transform messy resume text into clean, high-impact Markdown resumes optimized for ATS and recruiters."
        )
        writer_prompt = (
            f"Rewrite the candidate's resume based on the original resume text and advisor recommendations.\n\n"
            f"Original Resume:\n{resume_text}\n\n"
            f"Advisor Feedback:\n{feedback_output}\n\n"
            "Instructions:\n"
            "- Use clean Markdown hierarchy (# Name, ## Professional Summary, ## Key Skills, ## Experience, ## Education, ## Projects).\n"
            "- Transform passive bullet points into strong action verbs with measurable metrics.\n"
            "- Do NOT fabricate false work history or false facts.\n"
            "- Return ONLY the formatted Markdown resume."
        )
        print("🤖 Running Agent 2: Resume Writer...")
        improved_resume_output = safe_call_llm(selected_model, groq_key, writer_system, writer_prompt)
        time.sleep(1)

        # Agent 3: Job Researcher
        live_search_data = search_serper_jobs("Software Engineer", target_location, serper_key)

        researcher_system = (
            "You are a Senior Technical Recruitment Consultant. "
            "You analyze candidate profiles and match them with high-potential target roles and job opportunities."
        )

        search_context = f"\nLive Search Results:\n{live_search_data}\n" if live_search_data else ""

        researcher_prompt = (
            f"Based on the candidate's background and preferred location ({target_location}), recommend 5 target job positions.\n\n"
            f"Candidate Resume Summary:\n{resume_text[:1200]}\n"
            f"{search_context}\n"
            "Format the output as a Markdown report containing:\n"
            "1. **Top 5 Matching Job Roles** (Title, Required Key Skills, Industry Fit, Target Companies)\n"
            "2. **Application & Positioning Strategy** for {target_location}\n"
            "3. **Recommended Skill Upgrades** to boost callback rates."
        )
        print("🤖 Running Agent 3: Senior Recruitment Consultant...")
        job_roles_output = safe_call_llm(selected_model, groq_key, researcher_system, researcher_prompt)

        return feedback_output, improved_resume_output, job_roles_output

    except Exception as e:
        err_msg = f"### ❌ Execution Error\n\nAn error occurred while running the AI agents:\n\n```\n{str(e)}\n```"
        return err_msg, err_msg, err_msg


# Modern UI Styling
custom_css = """
body { font-family: 'Inter', sans-serif; }
.main-header { text-align: center; margin-bottom: 20px; }
.main-header h1 { font-size: 2.2rem; font-weight: 700; color: #1E293B; }
.main-header p { font-size: 1rem; color: #64748B; }
.submit-btn { background-color: #4F46E5 !important; color: white !important; font-weight: 600 !important; }
"""

with gr.Blocks(css=custom_css, title="AI Resume Builder & Job Matcher") as demo:
    with gr.Column(elem_classes=["main-header"]):
        gr.Markdown("# 🚀 AI Resume Optimizer & Job Matcher")
        gr.Markdown("Upload your resume (PDF/DOCX) to receive actionable feedback, an AI-rewritten resume, and curated job matches.")

    with gr.Row():
        with gr.Column(scale=1):
            resume_upload = gr.File(label="📄 Upload Resume (PDF or DOCX)", file_types=[".pdf", ".docx", ".txt"])
            location_input = gr.Textbox(label="📍 Preferred Location", placeholder="e.g. San Francisco, CA / Remote", value="Remote")
            
            model_dropdown = gr.Dropdown(
                label="🤖 AI Model",
                choices=["openai/gpt-oss-20b", "groq/compound-mini", "qwen/qwen3.6-27b", "qwen/qwen3.8-27b"],
                value="openai/gpt-oss-20b"
            )

            with gr.Accordion("🔑 API Key Settings (Optional if set in .env)", open=False):
                groq_key_input = gr.Textbox(
                    label="GROQ API Key",
                    placeholder="gsk_...",
                    type="password",
                    value=os.getenv("GROQ_API_KEY", "")
                )
                serper_key_input = gr.Textbox(
                    label="Serper API Key (Optional for live job search)",
                    placeholder="serper_...",
                    type="password",
                    value=os.getenv("SERPER_API_KEY", "")
                )

            submit_button = gr.Button("✨ Optimize Resume & Search Jobs", elem_classes=["submit-btn"], variant="primary")

        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.TabItem("📊 Resume Feedback"):
                    feedback_output = gr.Markdown("Upload your resume and click submit to generate feedback.")
                with gr.TabItem("📝 Rewritten Resume"):
                    improved_resume_output = gr.Markdown("Your optimized markdown resume will appear here.")
                with gr.TabItem("🎯 Job Opportunities"):
                    job_roles_output = gr.Markdown("Matching job positions and recommendations will appear here.")

    submit_button.click(
        fn=resume_agent,
        inputs=[resume_upload, location_input, groq_key_input, serper_key_input, model_dropdown],
        outputs=[feedback_output, improved_resume_output, job_roles_output]
    )

if __name__ == "__main__":
    demo.queue()
    demo.launch(server_name="0.0.0.0", share=False)