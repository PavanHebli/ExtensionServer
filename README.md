# 🚀 Extension Server

## 📌 Overview
Welcome to the **Extension Server**, the backend powerhouse for a Chrome extension that revolutionizes Google Search by providing **AI-generated summaries** tailored to user queries. This backend is built using **FastAPI** and performs the following key functions:

✅ **Receives search result URLs** from the Chrome extension via the `/summary` API.
✅ **Scrapes webpage content** using Selenium.
✅ **Processes the data with an LLM** to generate a **concise and query-relevant summary**.

## 🎯 Features
- 🌍 **Web API**: FastAPI-based server handling search result processing.
- 🔍 **Web Scraping**: Automates webpage content extraction with Selenium.
- 🧠 **LLM Integration**: Transforms raw web content into **meaningful summaries**.
- ⚡ **Enhanced Search Experience**: Provides **direct answers** to user queries, improving information retrieval efficiency.

## 🛠 Tech Stack
- **FastAPI**: High-performance API framework.
- **Selenium**: Web scraping for dynamic content extraction.
- **Large Language Model (Llama models)**: AI-powered summarization of scraped data.

## 📥 Installation Guide
### Prerequisites
Ensure you have the following installed:
- 🐍 Python 3.10+
- 📦 pip (Python package manager)
- 🌐 Chrome WebDriver (compatible with your Chrome browser version)

### Setup Instructions
1️⃣ **Clone the repository**:
   ```bash
   git clone https://github.com/PavanHebli/ExtensionServer.git
   cd ExtensionServer
   ```
2️⃣ **Create a virtual environment** *(optional but recommended)*:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
3️⃣ **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4️⃣ **Run the server**:
   ```bash
   uvicorn server:app --reload
   ```
   🎯 The API will be accessible at **`http://127.0.0.1:8000`**

## 🔗 API Usage
### **📌 POST /summary**
**Description**: Accepts a list of URLs, scrapes their content, and returns a summarized response.

#### **🔻 Request Body**
```json
{
  "urls": ["https://example.com/article1", "https://example.com/article2"]
}
```

#### **🔺 Response Example**
```json
"<summary_content>@@<related_questions>"
```

- The response is a string where:
  - `<summary_content>` contains the summarized content.
  - `<related_questions>` contains additional related questions.
- The client-side script splits the response using `"@@"` to extract and display the summary.

## 🤝 Contribution
Contributions are **welcome**! Feel free to submit issues or pull requests.

## 📜 License
📝 **MIT License** - Free to use and modify.

---

💌 For any inquiries, feel free to reach out to pavanhebli@gmail.com. Happy coding! 🎉