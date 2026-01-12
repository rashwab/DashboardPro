# DashboardPro

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.3-orange?logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3.41-lightgrey?logo=sqlite&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple?logo=bootstrap&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.1-blue?logo=pandas&logoColor=white)
![Chart.js](https://img.shields.io/badge/Chart.js-4.4-orange?logo=chart.js&logoColor=white)

**DashboardPro** is a Python-based web dashboard built with **Flask**, **Bootstrap 5**, and **Chart.js**. It allows users to view KPI performance, sales data, employee efficiency, manage tasks, and communicate via messages. The application supports **SQLite database** storage with an **Excel fallback** for offline or initial setups.

---

## Features

- **User Authentication**
  - Login via SQLite database or Excel file
  - Session-based authentication
- **Dashboard**
  - KPI performance over time (line chart)
  - Sales units per product (bar chart)
  - Top 5 employees by efficiency (bar chart)
  - Task status overview (doughnut chart)
- **Task Management**
  - Add, update, and delete tasks
  - User-specific task filtering
- **Messaging**
  - View conversations
  - Read messages in chronological order
  - Preview latest message per conversation
- **Settings**
  - User-specific settings page (currently static)
- **Excel Fallback**
  - Reads data from `plswork.xlsx` if database tables are empty or missing

---

## Default Login Credentials

> Use the following credentials to log in for testing:

- **Username:** `Alice`  
- **Password:** `pass123`

---

## Technologies Used

- **Backend:** Python, Flask  
- **Database:** SQLite (`app.db`)  
- **Frontend:** HTML (Jinja2 templates), Bootstrap 5, Chart.js  
- **Data Handling:** Pandas for Excel file reading  
- **Security:** Passwords hashed with SHA256 (Excel fallback uses plaintext)

---

## Project Structure
DashboardPro/
│
├── app.py # Main Flask application
├── app.db # SQLite database
├── plswork.xlsx # Excel data file for fallback
├── requirements.txt # Python dependencies
├── templates/ # HTML templates (login, index, tasks, messages, settings)
├── static/ # CSS, JS, and images
│ └── styles.css
└── README.md # Project documentation


---

## Setup Instructions

1. **Clone the repository**

```bash
git clone https://github.com/rashwab/DashboardPro-.git
cd DashboardPro-

python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

export FLASK_SECRET_KEY='your_secret_key_here'  # Windows: set FLASK_SECRET_KEY=your_secret_key_here

python app.py

