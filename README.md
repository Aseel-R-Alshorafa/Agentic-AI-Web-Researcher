# 🧠 Agentic AI Researcher

An end-to-end **agent-based research system** that autonomously explores a topic, gathers information from the web, evaluates relevance, and produces a structured research report — all with a transparent, step-by-step Streamlit interface.

---

## 🚀 Features

- 🔍 **Autonomous Research Pipeline**
  - Selects the appropriate assistant
  - Generates search queries
  - Performs web searches
  - Scrapes and summarizes content
  - Evaluates relevance
  - Writes a final report

- 🧩 **Modular Agent Architecture**
  - `assistant_selector`
  - `web_researcher`
  - `report_writer`

- 🌐 **Web Intelligence**
  - DuckDuckGo search with fallback strategy
  - HTML scraping with BeautifulSoup
  - LLM-powered summarization

- 📊 **Streamlit UI**
  - Step-by-step tabs for each stage
  - Live progress updates (e.g. "Generating queries...")
  - Clean markdown report rendering

---

## 📁 Project Structure

.
├── agents/
│   ├── assistant_selector.py
│   ├── web_researcher.py
│   ├── report_writer.py
│
├── utils/
│   ├── web_searching.py
│   ├── web_scraping.py
│
├── models.py
├── prompts.py
├── streamlit_research_frontend.py
├── requirements.txt
└── .env

---

## ⚙️ Installation

Using `uv` (recommended):

```bash
uv venv
source .venv/bin/activate  # or Windows equivalent

uv pip install -r requirements.txt
uv pip install streamlit python-dotenv
```

---

## 🔑 Environment Setup

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_api_key_here
```

---

## ▶️ Running the App

```bash
streamlit run streamlit_research_frontend.py
```

---

## 🧪 Example Workflow

1. Enter a research question
2. The system:
   - selects an expert assistant
   - generates search queries
   - gathers and summarizes data
   - evaluates relevance (iteratively)
   - writes a final report
3. View each step in dedicated tabs
4. Download the final report

---

## 🧠 How It Works

The system uses a **LangGraph-based pipeline**:

User Question
   ↓
Assistant Selection
   ↓
Query Generation
   ↓
Web Search
   ↓
Summarization
   ↓
Relevance Evaluation
   ↓ (loop if needed)
Report Writing

Relevance is evaluated, and if results are weak, the system **automatically regenerates better queries** (up to 3 iterations).

---

## 📌 Tech Stack

- **LangChain + LangGraph**
- **OpenAI (via `langchain-openai`)**
- **Streamlit**
- **DuckDuckGo Search API**
- **BeautifulSoup (HTML parsing)**
- **python-dotenv**

---

## ⚠️ Known Issues

- Requires a valid OpenAI API key
- Web scraping may fail on some sites (handled with fallback logic)
- Rate limits may trigger fallback search

---

## 📈 Future Improvements

- Streaming responses (real-time updates)
- Better source ranking
- Multi-agent collaboration
- Caching results
- Export to PDF

---

## 🤝 Contributing

Pull requests are welcome. For major changes, open an issue first to discuss what you’d like to change.

---

## 📄 License

MIT License
