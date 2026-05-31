# SmartRAD AI (DYYMA-AI)

## 📌 Introduction
SmartRAD AI is an intelligent web-based application developed to enhance service quality and operational efficiency in radiology departments. It optimizes the X-ray workflow and scheduling process through Artificial Intelligence (AI) and predictive analytics.

Acting as an external assistant layer alongside existing **RIS** (Radiology Information System) and **PACS** systems, SmartRAD AI requires no structural modifications to them. By analyzing real-time operational data—via HL7 messages and DICOM metadata—the system predicts scan durations and generates operational urgency scores for incoming cases to support smoother case progression, resource allocation, and reduced wait times.

## 🏗️ System Architecture
The application is built around five core components:
1. **HL7 Listener:** Receives real-time operational data from the RIS (exam requests, timestamps, scheduling details).
2. **DICOM Processor:** Extracts technical metadata directly from X-ray modalities (CR/DX) like acquisition timing and device identifiers.
3. **Prediction Engine:** Uses regression-based predictive models to estimate scan duration and generate an operational urgency score.
4. **Workflow Orchestration Engine:** Leverages prediction outputs, device availability, and workloads to dynamically organize and prioritize studies in the queue.
5. **Dashboard Interface:** Provides real-time workflow status, active case tracking, and operational performance insights.

## 📂 Project Structure
- **`app/`**: Flask web application housing the Dashboard UI, backend API routes, models, and static assets.
- **`mock_pacs/`**: Simulates incoming DICOM metadata.
- **`mock_ris/`**: Simulates incoming HL7 orders.
- **`scripts/`**: Operational scripts and data fillers (e.g., `fill_performance_data.py` for testing 14-day performance histories).
- **`run.py`**: The main entry point to launch the SmartRAD AI web server.
- **`xray.sql`**: The core operational database schema (MySQL/MariaDB) tracking history, rooms, users, and patients.
- **`requirements.txt`**: Python dependencies.

## 🚀 Installation & Setup
1. **Prerequisites:** Python 3.8+ and MySQL/MariaDB.
2. **Database Setup:** 
   Create a new database and import the `xray.sql` schema:
3. **Install Dependencies:**
   Run this command in terminal workspace:
   ```bash
   pip install -r requirements.txt
   ```
4. **Launch the Dashboard:**
   Start the application server:
   ```bash
   python run.py
   ```
   The dashboard will be available at `http://localhost:5000`.

## ⚙️ Features
- **Intelligent Case Sequencing:** Evaluates case urgency and queues patients dynamically for fair workload distribution.
- **Real-Time Dashboards:** Visualizes active scanning rooms, waiting queues, Critical Case alerts, system load, and average wait times.
- **Performance Analytics:** Tracks historical trends for scan durations, workload by modality (DX vs CR), and overall room utilization.
- **Testing Capabilities:** Comes with automated Mock RIS/PACS scripts to inject dummy cases directly into the system for testing without relying on a real hospital environment.

## 🛡️ Ethical Considerations & Compliance
- **Data Privacy:** Uses strictly anonymized, non-diagnostic operational and imaging metadata.
- **Scope Limitation:** SmartRAD AI strictly handles operational workflow optimization; it **does not** perform any clinical diagnosis or medical decision-making.
- **Human Oversight:** The system acts as a supportive decision engine—radiology technologists and supervisors retain the final authority to override automated case prioritizations.
