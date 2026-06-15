import streamlit as st
from groq import Groq
import os
import re
import PyPDF2
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.set_page_config(page_title="AI Study Buddy", page_icon="🤖", layout="wide")

# ── STYLES ───────────────────────────────────────────────────────────────────
def load_css(css_file):
    css_path = Path(__file__).resolve().parent / css_file
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

load_css("style.css")

# ── ERROR HELPERS ─────────────────────────────────────────────────────────────
def parse_rate_limit_wait(error_str):
    match = re.search(r"try again in (\d+)m([\d.]+)?s", error_str, re.I)
    if match:
        mins = int(match.group(1))
        secs = int(float(match.group(2) or 0))
        display = f"{mins} min" + (f" {secs}s" if secs else "")
        return display
    match = re.search(r"try again in ([\d.]+)s", error_str, re.I)
    if match:
        secs = int(float(match.group(1)))
        return f"{max(1, secs//60)} min"
    return "a few minutes"

def classify_error(error_str):
    err = error_str.lower()
    if "rate_limit" in err or "429" in err: return "rate_limit"
    if "401" in err or "invalid api key" in err: return "api_key"
    if "413" in err or "too large" in err: return "too_large"
    return "generic"

def clean_extracted_text(text):
    text = re.sub(r'(?<=[a-zA-Z])\n(?=[a-zA-Z])', ' ', text)
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def generate_quiz_pdf(quiz_data, title):
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from io import BytesIO

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1 # Center
    normal_style = styles['Normal']
    normal_style.spaceAfter = 10
    question_style = ParagraphStyle('Question', parent=styles['Normal'], fontName='Helvetica-Bold', spaceAfter=6)
    option_style = ParagraphStyle('Option', parent=styles['Normal'], leftIndent=20, spaceAfter=2)
    
    story = []
    
    # Title
    story.append(Paragraph(f"Quiz: {title}", title_style))
    story.append(Spacer(1, 12))
    
    # Student details
    story.append(Paragraph("Name: ________________________   Roll Number: ________________________", normal_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Marks: _______ / _______", normal_style))
    story.append(Spacer(1, 24))
    
    # Questions
    for i, q in enumerate(quiz_data):
        story.append(Paragraph(f"Q{i+1}. {q.get('question', '')}", question_style))
        options = q.get('options', {})
        for k, v in options.items():
            story.append(Paragraph(f"{k}) {v}", option_style))
        story.append(Spacer(1, 12))
        
    # Page Break for Answer Key
    story.append(PageBreak())
    story.append(Paragraph("ANSWER KEY", title_style))
    story.append(Spacer(1, 12))
    
    for i, q in enumerate(quiz_data):
        ans_text = f"<b>Q{i+1}: {q.get('answer', '')}</b> - {q.get('explanation', '')}"
        story.append(Paragraph(ans_text, normal_style))
        
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ── SESSION STATE ─────────────────────────────────────────────────────────────
for key, val in {
    "mode": "quiz",
    "result": None,
    "sessions_today": 0,
    "filename": None,
    "teacher_mode": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

mode_labels = {
    "quiz": "📝 Generate Quiz",
    "explain": "💡 Explain a Topic",
    "summary": "🔑 Key Points",
    "simplify": "🌍 Simplify Language",
}

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="navbar">
    <span style="font-size:1.6rem">🤖</span>&nbsp;
    <span class="nav-logo">AI <span>Study Buddy</span></span>
</div>
""", unsafe_allow_html=True)

# ── LAYOUT ────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1], gap="large")

with col1:
    st.markdown(f"""
    <div class="hero-card">
        <div class="hero-title">
            Welcome, Student! 😊 Let's Learn!
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Mode buttons
    st.markdown("<div class='section-title'>⚡ Choose a Mode</div>", unsafe_allow_html=True)
    st.radio(
        "Choose a Mode",
        options=["quiz", "summary", "explain", "simplify"],
        format_func=lambda x: mode_labels[x],
        horizontal=True,
        label_visibility="collapsed",
        key="mode"
    )

    st.divider()

    # Upload
    st.markdown("<div class='section-title'>📂 Upload Your Notes</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload PDF or TXT", type=["pdf","txt"], label_visibility="collapsed")

    notes_text = ""
    num_pages = 0
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            num_pages = len(pdf_reader.pages)
            raw_text = ""
            for page in pdf_reader.pages:
                raw_text += page.extract_text() or ""
            notes_text = clean_extracted_text(raw_text)
        else:
            notes_text = clean_extracted_text(uploaded_file.read().decode("utf-8"))
            num_pages = 1
        
        st.session_state.filename = uploaded_file.name
        
        st.markdown(f"""
        <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
            <h4 style="color: #166534; margin-top: 0; margin-bottom: 12px;">✅ Notes Ready</h4>
            <div style="color: #166534; font-size: 0.95rem; line-height: 1.5;">
                <div><strong>File Name:</strong> {uploaded_file.name}</div>
                <div><strong>Pages:</strong> {num_pages}</div>
                <div><strong>Characters Extracted:</strong> {len(notes_text):,}</div>
            </div>
            <hr style="border-color: #bbf7d0; margin: 12px 0;">
            <div style="color: #166534; font-size: 0.95rem;">
                <strong>Ready for:</strong>
                <ul style="margin: 4px 0 0 0; padding-left: 20px;">
                    <li>Interactive Quizzes</li>
                    <li>Topic Explanations</li>
                    <li>Key Point Summaries</li>
                    <li>Language Simplification</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.session_state.filename = None
        st.markdown("""
        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
            <h4 style="color: #334155; margin-top: 0; margin-bottom: 16px;">📚 Upload Your Study Notes</h4>
            <div style="display: flex; gap: 40px;">
                <div style="color: #475569; font-size: 0.95rem;">
                    <strong>Supported:</strong>
                    <ul style="margin: 4px 0 0 0; padding-left: 20px;">
                        <li>PDF</li>
                        <li>TXT</li>
                    </ul>
                </div>
                <div style="color: #475569; font-size: 0.95rem;">
                    <strong>Generate:</strong>
                    <ul style="margin: 4px 0 0 0; padding-left: 20px;">
                        <li>Interactive Quizzes</li>
                        <li>Topic Explanations</li>
                        <li>Key Point Summaries</li>
                        <li>Simplified Notes</li>
                    </ul>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Topic input
    topic = ""
    if st.session_state.mode == "explain":
        topic = st.text_input("🔍 Which topic to explain?", placeholder="e.g. Photosynthesis, Compiler Design...")

    st.divider()

    # ── GROQ FUNCTION ─────────────────────────────────────────────────────────
    def call_groq_chunked(prompt_template, notes, mode, chunk_size=6000, max_chunks=5):
        chunks = [notes[i:i+chunk_size] for i in range(0, len(notes), chunk_size)]
        chunks = chunks[:max_chunks]
        total = len(chunks)
        results = []

        # Single progress bar + single status text — reused each chunk
        progress_bar = st.progress(0)
        status = st.empty()

        for i, chunk in enumerate(chunks):
            pct = int((i / total) * 100)
            progress_bar.progress(pct)
            status.caption(f"⚡ Processing section {i+1} of {total}...")

            try:
                prompt = prompt_template.replace("{NOTES}", chunk)
                
                kwargs = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}]
                }
                if mode == "quiz":
                    kwargs["response_format"] = {"type": "json_object"}
                    
                response = client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content
                
                if mode == "quiz":
                    import json
                    try:
                        parsed = json.loads(content)
                        if "questions" in parsed:
                            results.extend(parsed["questions"])
                        elif isinstance(parsed, list):
                            results.extend(parsed)
                    except Exception as parse_e:
                        status.caption(f"⚠️ JSON parse error in section {i+1}, skipping...")
                else:
                    results.append(content)

            except Exception as e:
                err = str(e)
                kind = classify_error(err)

                if kind == "rate_limit":
                    wait = parse_rate_limit_wait(err)
                    progress_bar.empty()
                    status.empty()
                    st.markdown(f"""
<div class="error-card error-card--rate-limit">
    <div class="error-card__icon">⏳</div>
    <div class="error-card__title">You've hit the daily limit</div>
    <div class="error-card__body">
        The free Groq plan allows ~100k tokens per day. Your quota resets at midnight.
    </div>
    <div class="error-card__steps">
        ⏰ Wait <strong>{wait}</strong>, then click Generate again<br>
        📋 <strong>{len(results)} section(s)</strong> were processed — shown below
    </div>
</div>
                    """, unsafe_allow_html=True)
                    break

                elif kind == "api_key":
                    progress_bar.empty(); status.empty()
                    st.markdown("""
<div class="error-card error-card--api-key">
    <div class="error-card__icon">🔑</div>
    <div class="error-card__title">API key is not working</div>
    <div class="error-card__body">
        Your Groq API key is missing or expired.
    </div>
    <div class="error-card__steps">
        1. Visit <a href="https://console.groq.com" target="_blank">console.groq.com</a> → API Keys<br>
        2. Create a new key<br>
        3. Add it to your <code>.env</code> file as <code>GROQ_API_KEY=your_key</code><br>
        4. Restart the app
    </div>
</div>
                    """, unsafe_allow_html=True)
                    return None

                elif kind == "too_large":
                    status.caption(f"⚠️ Section {i+1} too large, skipping...")
                    continue

                else:
                    status.caption(f"⚠️ Skipped section {i+1}, continuing...")
                    continue

        progress_bar.progress(100)
        status.empty()

        if not results:
            st.markdown("""
<div class="error-card error-card--no-results">
    <div class="error-card__icon">😕</div>
    <div class="error-card__title">No results could be generated</div>
    <div class="error-card__body">
        This can happen if your API key is invalid or the daily limit was already reached.
    </div>
    <div class="error-card__steps">
        🔑 Check your API key in <code>.env</code><br>
        ⏳ Wait if limit reached — resets at midnight<br>
        📄 Try a smaller document
    </div>
</div>
            """, unsafe_allow_html=True)
            return None

        if mode == "quiz":
            st.session_state.sessions_today += 1
            return {"questions": results}

        if len(results) == 1:
            st.session_state.sessions_today += 1
            return results[0]

        status.caption("🔗 Combining all sections...")
        try:
            combined = "\n\n---\n\n".join(results)
            if mode == "summary":
                combine_prompt = f"Combine these key points into one clean, structured summary without duplicates:\n\n{combined}"
            elif mode == "simplify":
                combine_prompt = f"Combine these simplified sections into one cohesive, simple text:\n\n{combined}"
            elif mode == "explain":
                combine_prompt = f"Combine these explanations into one clean, structured answer without duplicates:\n\n{combined}"
            else:
                combine_prompt = f"Combine into one clean answer, no duplicates:\n\n{combined}"
                
            final = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": combine_prompt}]
            )
            st.session_state.sessions_today += 1
            status.empty()
            return final.choices[0].message.content
        except Exception as e:
            status.empty()
            if classify_error(str(e)) == "rate_limit":
                wait = parse_rate_limit_wait(str(e))
                st.markdown(f"""
<div class="error-card error-card--rate-limit">
    <div class="error-card__icon">⏳</div>
    <div class="error-card__title">Limit hit while combining sections</div>
    <div class="error-card__body">
        Wait <strong>{wait}</strong> then try again. Showing sections individually below.
    </div>
</div>
                """, unsafe_allow_html=True)
            return "\n\n---\n\n".join(results)

    # ── GENERATE BUTTON & RESULT MANAGEMENT ──────────────────────────────────
    if st.session_state.result:
        st.info("💡 **You already have an active result.**")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.button("▶️ Continue Reading/Quiz", use_container_width=True)
        with c2:
            if st.button("🔄 Generate New", use_container_width=True):
                st.session_state.result = None
                st.session_state.quiz_submitted = False
                st.rerun()
        with c3:
            if st.button("🗑️ Clear Result", use_container_width=True):
                st.session_state.result = None
                st.session_state.quiz_submitted = False
                st.rerun()
    else:
        if st.button("✨  Generate Now →", type="primary", use_container_width=True, key="generate"):
            if not notes_text:
                st.warning("👆 Upload a PDF or TXT file first, then click Generate!")
            else:
                st.session_state.result = None
                st.session_state.quiz_submitted = False
                mode = st.session_state.mode

                templates = {
                    "quiz": """Generate 5 multiple choice questions from these notes.
You MUST respond with a pure JSON object. No markdown, no explanations outside JSON.
The JSON must have a single key "questions" containing an array of question objects.
Format exactly like this:
{
  "questions": [
    {
      "question": "What is AI?",
      "options": {
        "A": "Database",
        "B": "AI System",
        "C": "Network",
        "D": "Compiler"
      },
      "answer": "B",
      "explanation": "AI stands for Artificial Intelligence."
    }
  ]
}

Notes:\n{NOTES}""",

                    "summary": """Extract key points from these notes.
Bold headers, bullet points, concise.

Notes:\n{NOTES}""",

                    "simplify": """Rewrite in very simple English.
Short sentences, no jargon, friendly tone.

Notes:\n{NOTES}""",
                }

                if mode == "explain":
                    t = topic if topic else "the main topic"
                    template = f"Explain '{t}' simply with a real-world analogy based on these notes.\n\nNotes:\n{{NOTES}}"
                else:
                    template = templates[mode]

                result = call_groq_chunked(template, notes_text, mode)
                st.session_state.result = result
                if result:
                    st.toast("✅ Done! Your results are ready", icon="✅")
                    if mode == "quiz":
                        st.balloons()

    # ── RESULT ────────────────────────────────────────────────────────────────
    if st.session_state.result:
        is_quiz = isinstance(st.session_state.result, dict)
        if is_quiz:
            quiz_data = st.session_state.result.get("questions", [])
            teacher_mode = st.session_state.get("teacher_mode", False)
            
            if teacher_mode:
                st.markdown("### 👨‍🏫 Teacher Mode: Printable Quiz Preview")
                st.markdown("---")
                for i, q in enumerate(quiz_data):
                    st.markdown(f"**Q{i+1}. {q.get('question', '')}**")
                    for k, v in q.get('options', {}).items():
                        st.markdown(f"{k}) {v}")
                    st.markdown(f"✅ **Answer:** {q.get('answer', '')} — {q.get('explanation', '')}")
                    st.markdown("---")
                
                pdf_bytes = generate_quiz_pdf(quiz_data, st.session_state.filename or "Quiz")
                st.download_button(
                    "📄 Download Quiz PDF",
                    data=pdf_bytes,
                    file_name="quiz.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.markdown("### 📝 Interactive Quiz")
                
                if "quiz_submitted" not in st.session_state:
                    st.session_state.quiz_submitted = False
                    
                with st.form("quiz_form"):
                    user_answers = {}
                    for i, q in enumerate(quiz_data):
                        st.markdown(f"**Q{i+1}. {q.get('question', '')}**")
                        options = [f"{k}) {v}" for k, v in q.get('options', {}).items()]
                        user_answers[i] = st.radio("Select answer", options, key=f"q_{i}", index=None, label_visibility="collapsed")
                        st.markdown("---")
                        
                    submitted = st.form_submit_button("Submit Quiz", use_container_width=True)
                    if submitted:
                        st.session_state.quiz_submitted = True
                        st.session_state.user_answers = user_answers
                        st.rerun()
                        
                if st.session_state.get("quiz_submitted", False):
                    score = 0
                    st.markdown("### 📊 Quiz Results")
                    user_answers = st.session_state.user_answers
                    
                    for i, q in enumerate(quiz_data):
                        ans_str = user_answers.get(i)
                        ans_key = ans_str.split(")")[0] if ans_str else None
                        
                        if ans_key == q.get("answer"):
                            score += 1
                            st.success(f"**Q{i+1}. {q.get('question', '')}**\n\n✅ Your answer: {ans_str} (Correct)\n\n*Explanation: {q.get('explanation', '')}*")
                        else:
                            st.error(f"**Q{i+1}. {q.get('question', '')}**\n\n❌ Your answer: {ans_str or 'None'} | Correct: {q.get('answer', '')}) {q.get('options', {}).get(q.get('answer', ''), '')}\n\n*Explanation: {q.get('explanation', '')}*")
                            
                    st.metric("Final Score", f"{score} / {len(quiz_data)}", f"{int(score/len(quiz_data)*100)}%")
        else:
            st.markdown("""
            <div class="result-shell">
                <span class="result-badge">🤖 AI RESPONSE</span>
            </div>
            """, unsafe_allow_html=True)
            res_text = st.session_state.result
            if isinstance(res_text, dict):
                import json
                res_text = json.dumps(res_text, indent=2)
            st.markdown(res_text)
            st.download_button(
                "📥 Download Result",
                data=res_text,
                file_name="studybuddy_result.txt",
                mime="text/plain",
                use_container_width=True
            )

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with col2:
    st.markdown("<div class='section-title'>⚙️ Settings</div>", unsafe_allow_html=True)
    st.toggle("👨‍🏫 Teacher Mode", key="teacher_mode", help="Enable printable PDF export for teachers")
    st.divider()

    st.divider()
    st.markdown("""
    <div class="tips-card">
        <div class="tips-card__title">💡 Quick Tips</div>
        <div class="tips-card__item">📄 PDF notes give best results</div>
        <div class="tips-card__item">🎯 Focused notes = better quiz</div>
        <div class="tips-card__item">⏳ Free limit: 100k tokens/day</div>
        <div class="tips-card__item">🔑 Key Points uses fewest tokens</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
