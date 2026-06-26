# SavvyCortex App  

A comprehensive React + FastAPI–based data cleaning and analytics tool from **Savvy Analytics** that helps businesses and analysts quickly prepare datasets, run automated analysis, and generate professional reports.  

![Savvy Analytics](https://img.shields.io/badge/Savvy%20Analytics-SavvyClean-blue) ![React](https://img.shields.io/badge/React-18.2.0-blue) ![Vite](https://img.shields.io/badge/Vite-5.0-purple) ![TypeScript](https://img.shields.io/badge/TypeScript-5.2-3178C6) ![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-3.3.0-38B2AC) ![shadcn/ui](https://img.shields.io/badge/shadcn/ui-Components-black) ![Python](https://img.shields.io/badge/Python-3.11-yellow) ![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688) ![License](https://img.shields.io/badge/License-Proprietary-red)  

Overview

SavvyCortex is a data cleaning and analytics application that combines a React/Vite + TypeScript frontend with a Python/FastAPI backend. It enables businesses, analysts, and product owners to:

Clean messy datasets with ML-powered strategies

Run automated analytics pipelines

Ask natural-language questions about their data

Generate professional reports for decision-making

Features
✨ Core Functionality

Data Uploads: CSV, Excel, JSON support

Intelligent Cleaner: Profiles your dataset and auto-selects the best cleaning strategy

Analytics Engine: Natural-language query interface for data analysis

Report Generation: Summaries, recommendations, and export options

Compliance Ready: Built with GDPR/AI Act awareness

Responsive UI: Tailwind CSS + shadcn/ui

📄 Footer Pages Implementation

All footer-linked pages are scaffolded with consistent styling and responsive design:

Product Pages: Features, Pricing, Testimonials, API (beta)

Resources: Documentation, Guides, API Reference, Blog

Company: About, Careers, Contact, Savvy Analytics info

Style Consistency: Dark/light theme, SEO-friendly, unified brand tokens

Installation
1. Clone the repository
git clone https://github.com/YOUR_USERNAME/savvycleanse.git
cd savvycleanse

2. Install dependencies (Frontend)
npm install
npm run dev


Frontend will start at http://localhost:5173
.

3. Setup Backend (FastAPI)
cd backend
pip install -r requirements.txt
uvicorn main:app --reload


Backend will run at http://localhost:8000
.

Available endpoints:

/upload → upload dataset

/clean → intelligent cleaning pipeline

/analyze → natural-language analytics

/report/summary → generate reports

/export → export cleaned data

File Structure
savvycleanse/
├── frontend/               # React + Vite frontend
│   ├── src/
│   └── public/
├── backend/                # FastAPI backend
│   ├── main.py
│   └── requirements.txt
├── package.json
└── README.md

Technologies Used

Frontend: React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui, Lucide React

Backend: Python 3.11, FastAPI, Pandas, ML-powered cleaning pipeline

Dev Tools: Lovable, GitHub Codespaces, Docker-ready configs

Deployment
Backend

Deploy to Render, Railway, Fly.io, or Docker:

uvicorn main:app --host 0.0.0.0 --port 8000

Frontend
npm run build


Deploy dist/ to Netlify, Vercel, or GitHub Pages.

Custom Domain

Connect via Project > Settings > Domains in Lovable.

Roadmap

 Expand API with more endpoints

 Add PDF report export

 Integrate vector database for semantic queries

 Multi-user authentication & role-based access

 Self-healing pipelines (data drift detection + correction)

License

© 2025 Savvy Analytics LLC. All rights reserved.

Contact

For support or inquiries:
Savvy Analytics
🌐 savvyanalytics.info
