# 🚀 NL to SQL Agent

> Convert natural language into SQL queries safely using LLMs.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red.svg)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)
![Ollama](https://img.shields.io/badge/LLM-Ollama-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 📸 Demo Preview

<img width="940" height="446" alt="image" src="https://github.com/user-attachments/assets/abda481f-d227-4659-bade-df6c6844451a" />


## Database/Schema section

<img width="940" height="398" alt="image" src="https://github.com/user-attachments/assets/1a9ff89c-77e6-4cc4-a17a-77bc329ff75a" />


## generated query

<img width="940" height="904" alt="image" src="https://github.com/user-attachments/assets/f93de2d3-4a1c-4ef7-a282-b60a57d02941" />

## available schemas

<img width="933" height="1241" alt="image" src="https://github.com/user-attachments/assets/bd7b9f0f-8732-4196-a237-b87e7e4c6c48" />

---

## 🧠 Overview

**NL to SQL Agent** is a lightweight AI-powered application that translates **natural language queries into SQL** and executes them securely on a SQLite database.

It uses **Ollama (LLaMA 3.2)** for SQL generation and ensures **safe, read-only query execution**.

---

## ✨ Features

- 🗣️ Natural Language → SQL conversion  
- 🔁 Auto query correction (retry on failure)  
- 🧩 Schema-aware SQL generation  
- 🔒 Safe execution (read-only mode)  
- 📊 Interactive UI with Streamlit  

---

## 🏗️ Project Structure

```bash
nl-sql/
│── app.py                  # Streamlit UI
│── config.py               # App & Ollama settings
│── db_utils.py             # Schema + validation + execution
│── nl_sql_engine.py        # SQL generation logic
│── requirements.txt        # Dependencies
│── data/
│   └── demo_nl_sql.sqlite  # Default database
│── assets/
│   └── demo.png            # Screenshots (optional)
````

---

## ⚙️ Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/nl-sql-agent.git
cd nl-sql-agent
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Run Ollama (LLaMA 3.2)

```bash
ollama run llama3.2
```

### 4️⃣ Start the App

```bash
streamlit run app.py
```

---

## 🗄️ Database Usage

* Default DB:

```bash
data/demo_nl_sql.sqlite
```

* Replace with your own SQLite DB via the **sidebar option**

---

## 🔒 Safety

This app is **read-only by design**.

### ✅ Allowed

* `SELECT`

### ❌ Blocked

* `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `CREATE`, `PRAGMA`

### ⚠️ Rules

* Only **single query at a time**
* No schema modifications allowed

---

## 🔁 Retry Mechanism

If SQL fails:

* System retries **once**
* Uses:

  * Error message
  * Database schema

---

## 🛠️ Tech Stack

| Layer    | Technology         |
| -------- | ------------------ |
| Frontend | Streamlit          |
| Backend  | Python             |
| Database | SQLite             |
| AI Model | Ollama (LLaMA 3.2) |

---

## 🚧 Future Enhancements

* 🔐 Admin mode (controlled write access)
* 📜 Query history & logging
* ☁️ Multi-database support
* 📊 Visualization of results

---

## 🤝 Contributing

Pull requests are welcome!
For major changes, open an issue first.

---

## 📜 License

This project is licensed under the **MIT License**.

---

## 💡 Author

**Om Rasal**
🎓 MCA Student | Data Analyst | AI/ML Enthusiast


