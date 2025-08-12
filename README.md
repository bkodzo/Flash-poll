# Flash Poll

A real-time polling application built with **Django**, **Django Channels**, **Redis**, and **Celery**, containerized with **Docker** for easy deployment.

## 🚀 Features
- **Real-time voting updates** using WebSockets (Channels + Redis)
- **Scheduled tasks** with Celery Beat
- **PostgreSQL database** for data persistence
- **Fully containerized** with Docker & Docker Compose
- **Environment-based configuration** using `python-dotenv`

## 🛠 Tech Stack
- **Backend**: Django 5.x, Django Channels 4.x
- **Asynchronous Layer**: Channels + Redis
- **Database**: PostgreSQL
- **Task Queue**: Celery + Redis broker
- **Containerization**: Docker & Docker Compose

## 📦 Getting Started

### Prerequisites
- Docker & Docker Compose installed
- Python 3.13+ (if running locally without Docker)

### Installation (Docker)
```bash
git clone https://github.com/bkodzo/Flash-poll.git
cd Flash-poll

# Copy .env example
cp .env.example .env

# Start services
docker compose up --build

The app will be available at:
http://localhost:8000
Local Development (without Docker)
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
Running Tests
pytest
 WebSocket API
WebSocket URL:
ws://localhost:8000/ws/poll/<poll_id>/
Message format:
{
  "type": "vote",
  "choice_id": 1
}
 Roadmap
 User authentication
 Poll expiration scheduling
 Docker production build with Nginx
 Frontend enhancements
 License
MIT License

---

### Steps to add it:
```bash
# From your project root
echo "<paste the above markdown>" > README.md
git add README.md
git commit -m "Add README"
git push
