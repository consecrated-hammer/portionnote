# Contributing to Portion Note

Thanks for helping improve Portion Note. This guide covers the basics for contributing.

## Code of Conduct

- Be respectful and considerate.
- Focus on constructive feedback.
- Keep discussions solution focused.

## How to Contribute

### Reporting Bugs

Before creating an issue:
- Search existing issues
- Provide steps to reproduce
- Include expected vs actual behavior
- Share environment details (OS, browser, Docker version)
- Attach relevant logs

### Suggesting Features

- Explain the user problem
- Describe the proposed solution
- Note any edge cases or tradeoffs

### Submitting Code

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Add or update tests
5. Run relevant checks
6. Open a pull request

## Development Setup

### Prerequisites

- Docker and Docker Compose
- Node.js 20+
- Python 3.11+

### Quick Start

```bash
git clone https://github.com/your-org/portionnote.git
cd portionnote
cp .env.example .env
docker compose up --build
```

### Backend (without Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:App --reload --port 8001
```

### Frontend (without Docker)

```bash
cd frontend
npm install
npm run dev
```

## Coding Standards

### Python (Backend)

- Use type hints
- Keep functions small and focused
- Prefer pure functions for calculations

### React (Frontend)

- Use functional components with hooks
- Keep components small and composable
- Use Tailwind utilities for styling

## Tests

```bash
# Backend
./scripts/backend.sh test

# Frontend
./scripts/frontend.sh test
```

## Pull Requests

- Keep PRs focused and scoped
- Update docs for user facing changes
- Add tests where logic changes

Thanks for contributing.

