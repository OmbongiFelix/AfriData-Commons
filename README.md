# AfriData Commons

AfriData Commons is a platform designed to bridge the gap in AI training datasets by providing a centralized repository for African community-curated data. By allowing users to upload, manage, and discover datasets representing diverse African norms, cultures, and languages, the platform promotes inclusivity in data-driven systems.

---

## 🌍 Project Purpose

Modern AI systems often lack representation from African contexts, leading to biased outcomes. AfriData Commons addresses this by:

- Enabling users to upload datasets in various formats.
- Providing powerful search, filter, and recommendation tools.
- Promoting dataset discovery and accessibility within African communities.

---

## 🧩 Key Features

### 👤 User Management
- User registration with email verification.
- Secure login and authentication.
- Profile management (bio, contact, profile picture).

### 📂 Dataset Management
- Upload datasets with metadata (CSV, JSON, XML, etc.).
- Download datasets with format preservation.
- Dataset access control based on user roles.

### 🔍 Discovery & Search
- Search datasets by keyword, tags, or filters.
- Advanced search by date, file type, and user-specific filters.
- Personalized recommendations.

### 📈 Analytics
- View trending datasets and topics.
- Engagement-based recommendations.

---

## ⚙️ System Architecture

- **Frontend**: HTML/CSS/JS 
- **Backend**: Django + Django REST Framework
- **Database**: PostgreSQL
- **Search Engine**: Elasticsearch (planned)
- **Deployment**: Docker + CI/CD pipeline
- **Diagram**: See [`Documentation/erd.dot`](../Documentation/erd.dot)

---

## 🏗️ Installation & Setup

### Requirements
- Python 3.10+
- MySql
- pip / pipenv
- Graphviz (for ERD generation)

### Clone the Repository
```bash
git clone https://github.com/OmbongiFelix/AfriData-Commons.git
cd Afridata-Commons
