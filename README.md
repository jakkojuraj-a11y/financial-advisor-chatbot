# 💰 FinBot — Financial Advisor Chatbot

A **production-ready, domain-specific chatbot** powered by Google Gemini GenAI API, designed to provide financial education and guidance.

---

## 🏗️ Architecture

```
app/
├── core/           # Config, logging, security, exceptions
├── api/            # Gemini API client with retry logic
├── prompts/        # System prompts, topic templates, prompt builder
├── memory/         # Conversation history with token-aware trimming
├── services/       # Chat service orchestrator
└── main.py         # Streamlit UI entry point
```

**Key design principles:**
- **Layered architecture** — UI → Service → (Prompt + Memory + API)
- **Dependency inversion** — UI never calls the API directly
- **Config-driven** — all settings via `.env`, validated at startup
- **Security-first** — prompt injection defense, rate limiting, input sanitization

---

## 🚀 Quick Start

### 1. Clone & Setup
```bash
git clone <your-repo-url>
cd financial-advisor-chatbot
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure API Key
```bash
cp .env.example .env
# Edit .env and add your Gemini API key
```

### 3. Run
```bash
streamlit run app/main.py
```

### 4. Test
```bash
pytest tests/ -v
```

---

## 🐳 Docker Deployment

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f chatbot

# Stop
docker-compose down
```

---

## ☁️ AWS EC2 Deployment

### 1. Launch EC2 Instance
- **AMI:** Ubuntu 22.04 LTS
- **Type:** t3.small (minimum)
- **Storage:** 20GB
- **Security Group:** Open ports 22 (SSH), 8501 (Streamlit)

### 2. Setup on EC2
```bash
# SSH into instance
ssh -i your-key.pem ubuntu@<EC2-PUBLIC-IP>

# Install Python
sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip git

# Clone and setup
git clone <your-repo-url>
cd financial-advisor-chatbot
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env  # Add your API key

# Run with nohup (background process)
nohup streamlit run app/main.py \
    --server.port=8501 \
    --server.headless=true \
    --browser.gatherUsageStats=false \
    > chatbot.log 2>&1 &

# Access at http://<EC2-PUBLIC-IP>:8501
```

### 3. Production Setup (Nginx Reverse Proxy)
```bash
sudo apt install -y nginx

# Configure Nginx
sudo tee /etc/nginx/sites-available/chatbot << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/chatbot /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx
```

### 4. Process Manager (systemd)
```bash
sudo tee /etc/systemd/system/chatbot.service << 'EOF'
[Unit]
Description=Financial Advisor Chatbot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/financial-advisor-chatbot
Environment=PATH=/home/ubuntu/financial-advisor-chatbot/.venv/bin
ExecStart=/home/ubuntu/financial-advisor-chatbot/.venv/bin/streamlit run app/main.py --server.port=8501 --server.headless=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable chatbot
sudo systemctl start chatbot
```

---

## ✅ Production Checklist

| Category | Item | Status |
|----------|------|--------|
| **Security** | API key in .env (not hardcoded) | ✅ |
| **Security** | Prompt injection defense | ✅ |
| **Security** | Input sanitization | ✅ |
| **Security** | Rate limiting per session | ✅ |
| **Security** | Financial disclaimers | ✅ |
| **Security** | Non-root Docker user | ✅ |
| **Reliability** | API retry with backoff | ✅ |
| **Reliability** | Graceful error handling | ✅ |
| **Reliability** | Health checks | ✅ |
| **Observability** | Structured logging | ✅ |
| **Observability** | Token usage tracking | ✅ |
| **Performance** | Token-aware memory trimming | ✅ |
| **Performance** | Configurable rate limits | ✅ |
| **Testing** | Unit tests for all modules | ✅ |
| **Testing** | Mocked API tests | ✅ |
| **Deployment** | Docker support | ✅ |
| **Deployment** | EC2 guide with systemd | ✅ |

---

## 📁 Project Structure

```
financial-advisor-chatbot/
├── app/
│   ├── __init__.py
│   ├── main.py                  # Streamlit entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── gemini_client.py     # Gemini API wrapper
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── templates.py         # System & topic prompts
│   │   └── builder.py           # Dynamic prompt construction
│   ├── memory/
│   │   ├── __init__.py
│   │   └── conversation.py      # Chat history & trimming
│   ├── services/
│   │   ├── __init__.py
│   │   └── chat_service.py      # Orchestrator
│   └── core/
│       ├── __init__.py
│       ├── config.py            # Pydantic settings
│       ├── logger.py            # Structured logging
│       ├── security.py          # Sanitization & rate limiting
│       └── exceptions.py        # Custom exceptions
├── tests/
│   ├── __init__.py
│   ├── test_security.py
│   ├── test_prompt_builder.py
│   ├── test_memory.py
│   ├── test_gemini_client.py
│   └── test_chat_service.py
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🔮 Future Enhancements

- **Redis** for persistent session memory across restarts
- **FastAPI** backend for REST API access
- **RAG** integration with financial knowledge base
- **CI/CD** pipeline with GitHub Actions
- **Monitoring** with Prometheus + Grafana
- **SSL/TLS** with Let's Encrypt
- **Multi-language** support

---

## ⚠️ Disclaimer

This chatbot provides **educational financial information only**. It is not a substitute for professional financial advice. Always consult a qualified financial advisor for decisions specific to your situation.
