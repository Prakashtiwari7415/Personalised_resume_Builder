"""
AI Agents Core Engine: Orchestrates multi-agent AI resume analysis, rewriting, and job recommendation.
"""

import os
import re
import time
import requests
import litellm

def clean_markdown_reasoning(text):
    """Strips internal LLM thinking tags if present in model output."""
    if not text:
        return ""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()


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


def run_resume_pipeline(resume_text, target_location, groq_key, serper_key="", selected_model="openai/gpt-oss-20b"):
    """
    Runs the multi-agent resume analysis, rewrite, and job recommendation workflow.
    
    Returns:
        tuple: (feedback_output, improved_resume_output, job_roles_output)
    """
    target_location = target_location.strip() if target_location and target_location.strip() else "Remote / Flexible"

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
    print("🤖 Agent 1 (Resume Advisor) evaluating...")
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
    print("🤖 Agent 2 (Resume Writer) crafting Markdown resume...")
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
    print("🤖 Agent 3 (Senior Recruitment Consultant) finding matches...")
    job_roles_output = safe_call_llm(selected_model, groq_key, researcher_system, researcher_prompt)

    return feedback_output, improved_resume_output, job_roles_output
