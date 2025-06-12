# Newsletter Generator

An AI-powered newsletter generator for social housing communities in the UK that automatically finds and curates local events.

## Features

- 🏘️ **Community-Focused**: Specifically designed for social housing communities
- 🎯 **Location-Based**: Searches for events within a specified radius of a postcode
- 🤖 **AI-Powered**: Uses OpenAI to generate engaging newsletter content
- 💬 **Interactive Chat**: Chat with AI to customize the newsletter
- 👁️ **Live Preview**: See newsletter changes in real-time
- ✅ **Verification**: Built-in safeguards against AI hallucinations
- 📧 **Professional Output**: MJML-based responsive email templates

## Prerequisites

- Docker and Docker Compose
- OpenAI API Key

## Quick Start

1. Clone the repository
2. Copy `.env.example` to `.env` and add your OpenAI API key
3. Run `docker-compose up -d`
4. Access the application at `http://localhost:3000`

## Architecture

- **Backend**: FastAPI with MongoDB
- **Frontend**: React with TypeScript
- **AI**: OpenAI GPT-4
- **Email Templates**: MJML

## Development

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Production Deployment

1. Update environment variables in `.env`
2. Set secure `SECRET_KEY` in docker-compose.yml
3. Configure proper MongoDB authentication
4. Use HTTPS in production
5. Set up proper backup strategies

## License

MIT
