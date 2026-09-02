"""
Main Gradio Application Entrypoint for AI Resume Builder & Job Matcher.
"""

import os
import gradio as gr

from config import DEFAULT_MODEL, AVAILABLE_MODELS, DEFAULT_LOCATION
from extractors import extract_text_from_resume
from agents import run_resume_pipeline
from exporter import export_markdown, export_pdf


def process_resume(file_obj, location, groq_key_input="", serper_key_input="", model_choice=""):
    """
    Main Gradio handler for resume processing, feedback, rewrite, job matching, and file export.
    """
    groq_key = (groq_key_input or os.getenv("GROQ_API_KEY") or "").strip()
    serper_key = (serper_key_input or os.getenv("SERPER_API_KEY") or "").strip()

    if not groq_key:
        err_msg = (
            "### ⚠️ GROQ API Key Required\n\n"
            "Please enter your **GROQ API Key** in the **API Key Settings** accordion below, "
            "or configure `GROQ_API_KEY` in your `.env` file.\n\n"
            "👉 Get a free key at [console.groq.com](https://console.groq.com)"
        )
        return err_msg, err_msg, err_msg, None, None

    if not file_obj:
        err_msg = "### ⚠️ Missing File\n\nPlease upload a resume file in PDF or DOCX format."
        return err_msg, err_msg, err_msg, None, None

    resume_text, extract_error = extract_text_from_resume(file_obj)
    if extract_error:
        err_msg = f"### ⚠️ File Error\n\n{extract_error}"
        return err_msg, err_msg, err_msg, None, None

    if not resume_text or len(resume_text.strip()) < 20:
        err_msg = "### ⚠️ Empty Resume\n\nCould not extract readable text from the uploaded file."
        return err_msg, err_msg, err_msg, None, None

    selected_model = model_choice.strip() if model_choice else DEFAULT_MODEL

    try:
        feedback, improved_resume, job_matches = run_resume_pipeline(
            resume_text=resume_text,
            target_location=location,
            groq_key=groq_key,
            serper_key=serper_key,
            selected_model=selected_model
        )

        # Generate download export files
        md_path = export_markdown(improved_resume, "optimized_resume.md")
        pdf_path = export_pdf(improved_resume, "optimized_resume.pdf")

        return feedback, improved_resume, job_matches, md_path, pdf_path

    except Exception as e:
        err_msg = f"### ❌ Execution Error\n\nAn error occurred while running the AI agents:\n\n```\n{str(e)}\n```"
        return err_msg, err_msg, err_msg, None, None


# Custom CSS Theme
custom_css = """
body { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
.main-header { text-align: center; margin-bottom: 24px; padding-top: 10px; }
.main-header h1 { font-size: 2.4rem; font-weight: 800; color: #0F172A; letter-spacing: -0.02em; }
.main-header p { font-size: 1.05rem; color: #475569; }
.submit-btn { background-color: #4F46E5 !important; color: white !important; font-weight: 600 !important; font-size: 1.05rem !important; border-radius: 8px !important; }
.download-btn { font-weight: 600 !important; border-radius: 8px !important; }
"""

with gr.Blocks(css=custom_css, title="AI Resume Builder & Job Matcher") as demo:
    with gr.Column(elem_classes=["main-header"]):
        gr.Markdown("# 🚀 AI Resume Optimizer & Job Matcher")
        gr.Markdown("Upload your resume (PDF/DOCX/TXT) to receive executive AI feedback, an ATS-rewritten resume, and targeted job opportunities.")

    with gr.Row():
        with gr.Column(scale=1):
            resume_upload = gr.File(label="📄 Upload Resume (PDF, DOCX, TXT)", file_types=[".pdf", ".docx", ".txt"])
            location_input = gr.Textbox(label="📍 Preferred Location", placeholder="e.g. San Francisco, CA / Remote", value=DEFAULT_LOCATION)
            
            model_dropdown = gr.Dropdown(
                label="🤖 AI Model Engine",
                choices=AVAILABLE_MODELS,
                value=DEFAULT_MODEL
            )

            with gr.Accordion("🔑 API Key Settings (Optional if configured in .env)", open=False):
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

            submit_button = gr.Button("✨ Optimize Resume & Find Jobs", elem_classes=["submit-btn"], variant="primary")

        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.TabItem("📊 Executive Resume Feedback"):
                    feedback_output = gr.Markdown("Upload your resume and click submit to generate executive feedback.")
                with gr.TabItem("📝 ATS-Rewritten Resume"):
                    improved_resume_output = gr.Markdown("Your optimized markdown resume will appear here.")
                    with gr.Row():
                        md_download = gr.File(label="📥 Download Markdown (.md)", interactive=False)
                        pdf_download = gr.File(label="📥 Download PDF (.pdf)", interactive=False)
                with gr.TabItem("🎯 Job Recommendations"):
                    job_roles_output = gr.Markdown("Matching job positions and strategy recommendations will appear here.")

    submit_button.click(
        fn=process_resume,
        inputs=[resume_upload, location_input, groq_key_input, serper_key_input, model_dropdown],
        outputs=[feedback_output, improved_resume_output, job_roles_output, md_download, pdf_download]
    )

if __name__ == "__main__":
    demo.queue()
    demo.launch(server_name="0.0.0.0", share=False)