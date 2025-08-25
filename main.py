import streamlit as st
from groq import Groq
import time
from fpdf import FPDF
import requests
from urllib.parse import quote

# ---------------------- API KEYS ----------------------
YOUTUBE_API_KEY = "AIzaSyCd8S1HOIuM60udY2PMkBIobqO1aGIQeVM"
# ------------------------------------------------------

# Initialize the Groq client
client = Groq()

# Page configuration
st.set_page_config(
    page_title="Mentora",
    layout="centered",
    initial_sidebar_state="collapsed",
    page_icon="📚",
)

# Custom CSS
st.markdown("""
    <style>
    .main { padding: 2rem; }
    .stButton>button { width: 100%; margin-top: 1rem; background-color: #FF4B4B; color: white; }
    .project-card { background-color: #f0f2f6; padding: 1.5rem; border-radius: 10px; margin: 1rem 0; }
    </style>
""", unsafe_allow_html=True)

# ---------------------- PDF Class ----------------------
class ProjectPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 24)
        self.cell(0, 20, 'Mentora', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        lines = body.split('\n')
        for line in lines:
            if line.strip().startswith('-'):
                self.cell(10)
                self.multi_cell(0, 8, line)
            else:
                self.multi_cell(0, 8, line)
        self.ln()

def create_pdf(topic, content):
    pdf = ProjectPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_title(f"Project Ideas - {topic}")
    pdf.set_author("Mentora")
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 10, f"Generated project ideas for: {topic}\n\n")
    projects = content.split("\n\n")
    for project in projects:
        if project.strip():
            pdf.multi_cell(0, 8, project)
            pdf.ln(4)
    output = pdf.output(dest="S")
    if isinstance(output, (bytes, bytearray)):
        return bytes(output)
    else:
        return output.encode("latin-1")

# ---------------------- YouTube Fetch Function (long videos only) ----------------------
def fetch_youtube_tutorials(query, max_results=5):
    url = (
        f"https://www.googleapis.com/youtube/v3/search?"
        f"part=snippet&q={quote(query)}+project+tutorial&type=video&"
        f"videoDuration=long&key={YOUTUBE_API_KEY}&maxResults={max_results}"
    )
    response = requests.get(url).json()
    videos = []
    for item in response.get("items", []):
        video_id = item["id"].get("videoId")
        if video_id:
            videos.append(f"https://www.youtube.com/watch?v={video_id}")
    return videos

# ---------------------- AI Step Generator ----------------------
def generate_project_steps(project_title):
    prompt = (
        f"Provide a clear step-by-step guide for building the project: '{project_title}'. "
        "Include coding steps, setup, and key concepts for learning."
    )
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an experienced tech mentor and project guide."},
                {"role": "user", "content": prompt},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_completion_tokens=2000,
            top_p=1,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"❌ Unable to generate steps: {str(e)}"

# ---------------------- AI Hints/Q&A ----------------------
def generate_project_hints(project_title):
    prompt = (
        f"Provide helpful hints, tips, and troubleshooting advice for the project: '{project_title}'. "
        "Keep it practical and beginner-friendly."
    )
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert project mentor providing hints."},
                {"role": "user", "content": prompt},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_completion_tokens=1000,
            top_p=1,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"❌ Unable to generate hints: {str(e)}"

# ---------------------- Main App ----------------------
st.title("Mentora 👩‍🏫")
st.markdown("""
Your AI mentor for project learning. Your personal AI-powered project coach.
From confusion to clarity – Mentora is here.
An AI mentor built to simplify project learning and fuel your growth.
""")

tabs = st.tabs(["Generate Projects", "Project Resources"])

# ---------------------- Tab 1: Generate Projects ----------------------
with tabs[0]:
    col1, col2 = st.columns(2)

    with col1:
        topic = st.text_input("🎯 Topic", placeholder="e.g. Machine Learning")
        hardness = st.select_slider("💪 Difficulty Level", options=["Beginner","Easy","Medium","Hard","Expert"], value="Medium")

    with col2:
        days = st.select_slider("⏱️ Completion Time", options=["7","14","30","60","90"], value="30")
        num_projects = st.slider("📚 Number of Projects", min_value=1, max_value=10, value=5)

    if st.button("🎮 Generate Project Ideas", use_container_width=True):
        if not topic.strip():
            st.error("🚫 Please enter a valid topic.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            for i in range(100):
                progress_bar.progress(i + 1)
                status_text.text(f"Generating project ideas... {i + 1}%")
                time.sleep(0.01)
            try:
                prompt = (
                    f"Generate {num_projects} unique projects to master '{topic}', each completed in {days} days with '{hardness}' difficulty. "
                    "Include title, description, learning outcomes, and main technologies."
                )
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are an experienced tech mentor."},
                        {"role": "user", "content": prompt},
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.7,
                    max_completion_tokens=10000,
                )
                progress_bar.empty()
                status_text.empty()
                st.success("🎉 Project ideas generated!")
                response = chat_completion.choices[0].message.content
                st.markdown("---")
                st.subheader("🎯 Your Personalized Project Ideas")
                st.markdown(response)

                # Save in session for tracking
                st.session_state.generated_projects = response.split("\n\n")

                pdf_text = response.replace("#", "").replace("*", "\t*")
                pdf_bytes = create_pdf(topic, pdf_text)
                st.download_button("📥 Download Project Ideas (PDF)", data=pdf_bytes, file_name=f"{topic}_project_ideas.pdf", mime="application/pdf")

            except Exception as e:
                st.error(f"❌ {str(e)}")

# ---------------------- Tab 2: Project Resources ----------------------
with tabs[1]:
    st.header("📚 Project Resources")
    project_title = st.text_input("Enter project title to fetch resources:", key="resource_topic")
    if st.button("Fetch Resources", key="fetch_resources"):
        if not project_title.strip():
            st.error("🚫 Enter a project title.")
        else:
            st.info("Fetching resources...")
            youtube_links = fetch_youtube_tutorials(project_title)
            steps = generate_project_steps(project_title)
            hints = generate_project_hints(project_title)

            st.subheader("🎥 YouTube Tutorials (Long Videos)")
            if youtube_links:
                for link in youtube_links:
                    st.write(f"[{link}]({link})")
            else:
                st.write("No tutorials found.")

            st.subheader("📝 Step-by-Step Guide")
            st.markdown(steps)

            st.subheader("💡 Hints & Tips")
            st.markdown(hints)

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
Made with ❤️ to help you learn better.<br>
Remember: The best project is the one you'll actually build!
</div>
""", unsafe_allow_html=True)
