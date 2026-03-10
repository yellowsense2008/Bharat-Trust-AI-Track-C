Bharat Trust AI – Track C

AI-Driven Grievance Redressal System

Developed by YellowSense Technologies Pvt Ltd

⸻

Overview

Bharat Trust AI – Track C is an AI-powered grievance redressal platform designed to automate and improve the complaint resolution journey for financial and public service systems.

The system uses Natural Language Processing (NLP), automation, and intelligent routing to categorize, prioritize, and route citizen complaints to the appropriate department while enabling regulators and institutions to detect systemic issues early.

This project is being developed as part of the RBI HaRBInger Innovation Hackathon.

⸻

Key Features

AI Complaint Processing
	•	Automatic complaint categorization using NLP
	•	Priority scoring based on severity keywords
	•	Intelligent department routing
	•	Duplicate complaint detection and clustering

Accessibility & Inclusivity
	•	Multilingual complaint support
	•	Designed to support voice-based interfaces (STT/TTS) in UI
	•	Accessible for senior citizens and users with limited digital literacy

Automated Assistance
	•	Known issue auto-resolution
(e.g., system downtime notifications)
	•	Instant automated responses for users

Monitoring & Governance
	•	Complaint timeline tracking
	•	SLA-based escalation detection
	•	Systemic complaint spike detection (possible outages or failures)

⸻

System Architecture

User Interface (Web / Mobile)
            ↓
     FastAPI Backend
            ↓
 AI Processing & Automation
            ↓
       PostgreSQL Database

Deployment-ready architecture:

Frontend (UI)
        ↓
Google Cloud Run (FastAPI)
        ↓
Google Cloud SQL (PostgreSQL)


⸻

Tech Stack

Backend Framework
	•	FastAPI

Database
	•	PostgreSQL

AI / NLP
	•	Scikit-learn
	•	TF-IDF Vectorization
	•	Cosine Similarity

Translation
	•	Deep Translator

Infrastructure
	•	Docker
	•	Google Cloud Platform (Cloud Run + Cloud SQL)

⸻

Project Structure

Track_C_Grievance-System
│
├── app
│   ├── api
│   │   └── complaint_routes.py
│   │
│   ├── core
│   │   ├── database.py
│   │   └── security.py
│   │
│   ├── models
│   │   ├── complaint.py
│   │   └── user.py
│   │
│   ├── schemas
│   │   └── complaint_schema.py
│   │
│   ├── services
│   │   ├── ai_service.py
│   │   ├── response_service.py
│   │   ├── known_issue_service.py
│   │   └── systemic_risk_service.py
│   │
│   └── main.py
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md


⸻

Running the Project Locally

1. Clone the repository

git clone https://github.com/yellowsense2008/bharat-trust-ai-track-c.git
cd bharat-trust-ai-track-c

2. Start the services using Docker

docker compose up --build

The backend API will be available at:

http://localhost:8000

Swagger API documentation:

http://localhost:8000/docs


⸻

Example API Flow

Submit Complaint

POST /complaints

{
"title": "Water pipeline leakage",
"description": "Pipeline broken near hospital road"
}

Response:

{
 "reference_id": "GRV-2026-0001",
 "department": "Water Department",
 "priority": 9
}


⸻

Track Complaint Timeline

GET /complaints/timeline/{reference_id}

⸻

Systemic Risk Detection

GET /complaints/systemic-risk

Detects spikes in complaints that may indicate system failures or outages.

Example response:

{
 "alerts": [
  {
   "category": "Utilities",
   "complaints": 9,
   "risk": "Possible service outage or systemic issue"
  }
 ]
}


⸻

Accessibility Vision

The platform is designed to support:
	•	Voice-based complaint submission
	•	Multilingual grievance reporting
	•	Simplified interfaces for elderly and digitally inexperienced users

These capabilities enable broader access to grievance redressal systems.

⸻

Future Enhancements
	•	Voice complaint submission (Speech-to-Text)
	•	Text-to-Speech response support
	•	AI-powered regulator dashboards
	•	Fraud pattern detection
	•	Cross-institution complaint clustering

⸻

License

This project is developed for the RBI HaRBInger Innovation Hackathon.

⸻

Developed By

YellowSense Technologies Pvt Ltd

AI systems for trust, governance, and digital infrastructure.
