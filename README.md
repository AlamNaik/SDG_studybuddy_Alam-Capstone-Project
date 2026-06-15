# AI Study Buddy

An AI-powered educational assistant designed to transform the way students learn from their own study materials. By leveraging advanced language models, AI Study Buddy helps students extract key concepts, test their knowledge, and simplify complex topics directly from their notes.

## 🎯 Problem Statement

Students often struggle when studying from long, dense notes or textbooks. Traditional revision methods lack interactive self-assessment, making it difficult to gauge understanding. Furthermore, many learners do not have access to personalized tutors or customized learning materials, which can slow down the learning process and reduce retention.

## 💡 Solution

AI Study Buddy serves as a personalized, always-available study companion. It empowers students to upload their own notes and instantly interact with the material. By generating dynamic quizzes, providing clear explanations, and summarizing key points, AI Study Buddy makes learning faster, more engaging, and highly effective.

## ✨ Features

- **Upload PDF or TXT:** Seamlessly ingest your own study materials.
- **Interactive Quiz Generation:** Create tailored quizzes based on the uploaded content.
- **Automatic Quiz Evaluation:** Get instant feedback and scoring on your quiz performance.
- **Topic Explanations:** Receive clear, AI-driven explanations for complex subjects.
- **Key Point Summaries:** Distill long documents into concise, easy-to-read summaries.
- **Simplified Notes:** Break down difficult concepts into simpler terms.
- **Teacher Mode:** A dedicated mode for educators to generate learning materials.
- **Printable Quiz PDF Export:** Export quizzes and answer keys for offline use.
- **Answer Key Generation:** Automatically generate answers for educators and students.
- **Friendly Error Handling:** Smooth user experience with clear guidance during issues.
- **Modern Responsive UI:** A clean, intuitive, and accessible interface built with Streamlit.

## 🛠️ Tech Stack

| Technology | Purpose |
| :--- | :--- |
| **Python** | Core application logic and backend processing |
| **Streamlit** | Building the modern, responsive web application interface |
| **Groq API** | High-speed inference API for powering AI features |
| **LLaMA Models** | The underlying large language models for text generation |
| **PyPDF2** | Extracting text from uploaded PDF study materials |
| **ReportLab** | Generating downloadable PDF quizzes and answer keys |
| **HTML/CSS** | Custom styling for a polished user experience |

## 📸 Screenshots

### Home Page
![Home Page](screenshot/Homepage.png)

### Quiz Generation
![Notes Upload](screenshot/NotesUpload.png)

### Interactive Quiz
*(Add Screenshot)*

### Teacher Mode
*(Add Screenshot)*

## 🚀 Installation

Follow these steps to set up the project locally:

```bash
git clone https://github.com/yourusername/Study_Buddy.git
cd Study_Buddy
pip install -r requirements.txt
streamlit run app.py
```

## 🔑 Environment Variables

To run the application, you need to configure your Groq API key. Create a `.env` file in the root directory and add the following:

```env
GROQ_API_KEY=your_api_key_here
```

> **Note:** Never commit your `.env` file or expose your API keys on GitHub. Ensure `.env` is included in your `.gitignore` file.

## 🌍 SDG Alignment

This project directly supports **Sustainable Development Goal 4 (SDG 4) – Quality Education**. By providing accessible, AI-driven educational tools, AI Study Buddy helps ensure inclusive and equitable quality education and promotes lifelong learning opportunities for all.

## 📂 Project Structure

```text
Study_Buddy/
├── .streamlit/
├── app.py
├── requirements.txt
├── style.css
└── README.md
```

## 🔮 Future Enhancements

- **Flashcards:** Auto-generate interactive flashcards for quick revision.
- **Multi-language Support:** Allow users to study in their preferred language.
- **Learning Analytics:** Track progress, strengths, and areas for improvement.
- **Voice-based Learning:** Incorporate speech-to-text and text-to-speech features.
- **Personalized Study Plans:** AI-generated schedules based on upcoming exams.

## 👨‍💻 Author

**Pranav Vivek Sadwelkar**

## 📜 License

MIT License
