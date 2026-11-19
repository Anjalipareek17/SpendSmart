# SpendSmart – Personal Finance & Budget Tracker

> **B.Tech Computer Science Major Project Submission**  
> Architected with a clean, decoupled 3-tier structure: **Frontend**, **Backend**, and **Database**.

---

## 🏛️ Project Architecture

```text
SpendSmart/
│
├── frontend/                     # PRESENTATION LAYER
│   ├── templates/                # HTML5 Jinja2 Templates
│   │   ├── base.html             # Master layout with responsive sidebar & modal
│   │   ├── index.html            # Dashboard with financial cards & charts
│   │   ├── transactions.html     # Filterable transaction table
│   │   ├── budgets.html          # Monthly budget limits & progress bars
│   │   └── reports.html          # Analytics, savings rate & category breakdown
│   └── static/                   # Static Assets
│       ├── css/
│       │   └── style.css         # Modern SaaS CSS (Navy/Emerald/White palette)
│       └── js/
│           └── script.js         # Vanilla JS: Chart.js render & modal logic
│
├── backend/                      # APPLICATION / BUSINESS LOGIC LAYER
│   ├── app.py                    # Flask server, controllers & REST API endpoints
│   ├── config.py                 # Application settings, categories & color palettes
│   └── requirements.txt          # Python dependencies
│
├── database/                     # DATA PERSISTENCE LAYER
│   ├── models.py                 # SQLAlchemy ORM Models (Transaction, Budget)
│   ├── schema.sql                # Pure SQL Schema (DDL) for faculty presentation
│   └── finance.db                # SQLite Relational Database (pre-seeded with demo data)
│
├── run.py                        # Single-command launcher (python run.py)
├── test_app.py                   # Automated Test Suite (Unittest)
├── Procfile                      # Production deployment configuration (Render/Railway)
├── requirements.txt              # Root dependencies
└── README.md                     # Academic project documentation
```

---

## 🚀 How to Run the Project in VS Code

### Step 1: Open in VS Code
1. Open **VS Code**.
2. Go to **File** ➔ **Open Folder...** ➔ Select `SpendSmart`.

### Step 2: Install Dependencies (if not already installed)
In the VS Code terminal (`Ctrl + ~`):
```powershell
python -m pip install -r requirements.txt
```

### Step 3: Run the Application
```powershell
python run.py
```
You will see:
```text
=======================================================
 SpendSmart - Personal Finance & Budget Tracker
 Web Server Running at: http://127.0.0.1:5000
 Press CTRL+C to quit
=======================================================
```

### Step 4: Open in Google Chrome
Visit: 👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🧪 Run Automated Tests
```powershell
python -m unittest test_app.py
```

---

## 📋 Faculty Viva Q&A Guide

1. **Why separate Frontend, Backend, and Database folders?**
   - It adheres to the **Separation of Concerns (SoC)** and **MVC (Model-View-Controller)** design pattern. The presentation layer (HTML/CSS/JS) is isolated from business rules (Flask routes), which are isolated from database entities (SQLAlchemy).
2. **How does data persist?**
   - All records are saved permanently in `database/finance.db` using **SQLite**. Even after stopping the server or restarting the laptop, all transactions and budgets are preserved.
3. **How are the 80% and 100% budget alerts calculated?**
   - Whenever an expense is added or deleted, the backend calculates the ratio:
     $$\text{Utilization} = \left(\frac{\text{Actual Category Spending}}{\text{Budget Limit}}\right) \times 100$$
     - $\ge 100\%$: High-severity Danger alert.
     - $80\% \le \text{ratio} < 100\%$: Warning alert.
4. **How are charts updated?**
   - The frontend uses **Chart.js** to fetch JSON asynchronously from the REST API endpoint `/api/charts`, rendering interactive Doughnut and 6-month Bar charts without full page refreshes.
