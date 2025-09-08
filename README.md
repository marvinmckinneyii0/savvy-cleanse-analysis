# SavvyClean: Data Cleaning & Data Analysis App

## Project info
URL: https://lovable.dev/projects/2ecea895-8960-4ad5-b705-0bc59bc94016

---

## 🚀 How can I edit this code?

There are several ways of editing your application:

### 1. Use Lovable
Simply visit the [Lovable Project](https://lovable.dev/projects/2ecea895-8960-4ad5-b705-0bc59bc94016) and start prompting.  
Changes made via Lovable will be committed automatically to this repo.

### 2. Use your preferred IDE
If you want to work locally using your own IDE:

```bash
# Step 1: Clone the repository using the project's Git URL.
git clone <YOUR_GIT_URL>

# Step 2: Navigate to the project directory.
cd <YOUR_PROJECT_NAME>

# Step 3: Install the necessary dependencies.
npm i

# Step 4: Start the development server with auto-reloading and an instant preview.
npm run dev
3. Edit a file directly in GitHub
Navigate to the desired file(s).

Click the "Edit" button (pencil icon) at the top right of the file view.

Make your changes and commit them.

4. Use GitHub Codespaces
Navigate to the main page of your repository.

Click on the Code button (green button).

Select the Codespaces tab.

Click on New codespace to launch an environment.

Edit files directly and commit/push when done.

🧹 How to clean/reset your repo
If you want to start fresh and avoid conflicts:

Option A: Keep Git history
bash
Copy code
cd /c/Users/marvi/github-projects/savvycleanse
git rm -r *
git commit -m "Remove old files for fresh scaffold"
git add .
git commit -m "Add new scaffold"
git push origin main
Option B: Start completely fresh (no history)
bash
Copy code
cd /c/Users/marvi/github-projects
rm -rf savvycleanse
git clone https://github.com/YOUR_USERNAME/savvycleanse.git
cd savvycleanse
🛠️ Technologies used
Vite

TypeScript

React

shadcn-ui

Tailwind CSS

Python (FastAPI backend)

🐍 Python Backend (FastAPI)
A FastAPI backend is provided in the backend directory.
It includes a data cleaning and analytics pipeline powered by machine learning.
Endpoints are exposed for uploading datasets, cleaning them, and answering analytics questions.

Setup
bash
Copy code
# Install Python dependencies
pip install -r backend/requirements.txt

# If you encounter a ModuleNotFoundError for pandas:
pip install pandas

# Run the API server
uvicorn main:app --reload
The API will start on http://localhost:8000.
You can interact with routes such as:

/upload

/clean

/goal

/analyze

/report/summary

/export

The /clean endpoint uses an intelligent cleaner that profiles your data and selects the best strategy automatically.
The /analyze endpoint accepts a natural language question about your dataset and returns the analytics type along with recommended next steps.

🌍 How can I deploy this project?
Deploy Backend (FastAPI)
Use Render, Railway, Fly.io, or Docker.

Deploy Frontend (React/Vite)
bash
Copy code
npm run build
Deploy the dist/ folder to Netlify, Vercel, or GitHub Pages.

Custom Domain
Yes! Navigate to Project > Settings > Domains and click Connect Domain.

## 📄 Footer Pages Implementation

**Footer pages scaffolded and content placeholders added.**

All footer-linked pages have been implemented with comprehensive content and consistent styling:

### Product Pages
- **Features** (`/features`) - Detailed feature descriptions with icons and benefits
- **Pricing** (`/pricing`) - Three-tier pricing structure with FAQ section
- **Testimonials** (`/testimonials`) - Customer testimonials with ratings and stats
- **API** (`/api`) - API overview, features, and code examples (Private Beta)

### Resources Pages  
- **Documentation** (`/documentation`) - Quick start guide and API examples
- **Guides** (`/guides`) - In-depth tutorials and learning resources
- **API Reference** (`/api-reference`) - Complete endpoint documentation
- **Blog** (`/blog`) - Company blog with featured posts and categories

### Company Pages
- **About** (`/about`) - Company mission, values, team, and timeline
- **Careers** (`/careers`) - Open positions with detailed job descriptions
- **Contact** (`/contact`) - Contact form, support info, and FAQ
- **Savvy Analytics** (`/savvy-analytics`) - Parent company information

### Implementation Details
- All pages follow consistent design patterns using Tailwind CSS and shadcn/ui components
- Proper React Router integration with working navigation
- Responsive design with mobile-first approach
- Dark/light theme support maintained
- SEO-friendly structure with proper headings and meta information
- Consistent use of Savvy brand colors (blue, gold, dark themes)

### Routing
Footer links now properly route to their respective pages using React Router `Link` components instead of placeholder anchor tags.
