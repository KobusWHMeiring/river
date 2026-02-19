# Tech Stack: River Project

## Backend
- **Framework:** Django 6.0.2
- **Language:** Python 3.x
- **Database:** SQLite (Development), PostgreSQL (Production target via `.env`)
- **Environment Management:** `python-environ`

## Frontend
- **Templating:** Django Template Language (DTL)
- **Styling:** Vanilla CSS (Custom styles in `static/css/`)
- **Interactivity:** Vanilla JavaScript (Native DOM APIs, minimal external dependencies)
- **Aesthetics:** Clean, professional, high information density, subtle borders, professional color palette.

## Infrastructure & Tools
- **Deployment:** `deploy.sh` (Shell script based deployment)
- **Feature Management:** `new-feature.sh`, `switch-feature.sh`, `sync-feature.sh`
- **Context Management:** `summarise.py` (Automated codebase summarization)
- **Documentation:** Markdown files in `product/context/` and `docs/`
