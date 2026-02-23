# Building a Production-Ready AI Financial Advisor Chatbot with Google Gemini

*A deep dive into architecture, security, and real-world engineering behind FinBot — a domain-specific chatbot that goes far beyond "hello world" tutorials.*

---

Large Language Models are powerful, but wrapping one in a production application requires much more than a simple API call. You need security layers, conversation memory, prompt engineering, and clean architecture to build something truly reliable.

In this post, I'll walk you through **FinBot** — an AI-powered financial advisor chatbot I built from scratch using Python, Streamlit, and Google's Gemini API. The full source code is open source on [GitHub](https://github.com/jakkojuraj-a11y/financial-advisor-chatbot).

> ⚠️ **Disclaimer:** FinBot provides educational financial information only. It is not a substitute for professional financial advice.

---

## Why Build This?

Most LLM chatbot tutorials stop at the "hello world" stage — a single API call with no error handling, no security, and no context management. I wanted to demonstrate **real-world engineering practices**:

- **Domain Expertise:** The bot stays focused on finance — it won't help you write poetry
- **Security:** Prompt injection defense, rate limiting, input sanitization
- **Memory:** Token-aware conversation history that doesn't blow up API costs
- **Clean Code:** Layered architecture with full test coverage
- **Deployment Ready:** Docker and AWS EC2 support out of the box

---

## Tech Stack

- **LLM:** Google Gemini 2.0 Flash — fast, capable, with system instructions support
- **Backend:** Python with Pydantic for type-safe configuration
- **UI:** Streamlit — beautiful chat interface with minimal code
- **Deployment:** Docker + docker-compose, AWS EC2 with Nginx & systemd
- **Testing:** pytest with fully mocked API calls

---

## Architecture: Strict Layering

The key design decision was **strict layering with dependency inversion**. The UI never calls the API directly — everything flows through the `ChatService` orchestrator.

```
Streamlit UI → ChatService → Prompt Builder + Memory + Security → Gemini API
```

**Key design principles:**

1. **Layered architecture** — UI → Service → (Prompt + Memory + API)
2. **Dependency inversion** — UI never calls the API directly
3. **Config-driven** — all settings via `.env`, validated at startup
4. **Security-first** — prompt injection defense, rate limiting, input sanitization

### Project Structure

```
financial-advisor-chatbot/
├── app/
│   ├── main.py                  # Streamlit entry point
│   ├── api/
│   │   └── gemini_client.py     # Gemini API wrapper with retry
│   ├── prompts/
│   │   ├── templates.py         # System & topic prompts
│   │   └── builder.py           # Dynamic prompt construction
│   ├── memory/
│   │   └── conversation.py      # Chat history & token trimming
│   ├── services/
│   │   └── chat_service.py      # Orchestrator
│   └── core/
│       ├── config.py            # Pydantic settings
│       ├── logger.py            # Structured logging
│       ├── security.py          # Sanitization & rate limiting
│       └── exceptions.py        # Custom exceptions
├── tests/                       # Full unit test suite
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## The Message Pipeline

Every user message goes through a **6-step pipeline** inside `ChatService.process_message()`:

1. **Sanitize Input** — strip control characters, limit length, check for prompt injection
2. **Rate Limit Check** — sliding window per session (10 req/min default)
3. **Build Prompt** — detect financial topics, assemble system instructions
4. **Retrieve Memory** — get token-trimmed conversation history
5. **Call Gemini API** — with retry + exponential backoff (3 attempts)
6. **Update Memory** — store user and model messages

```python
def process_message(self, user_input: str) -> str:
    # Step 1: Sanitize input
    sanitized = sanitize_input(user_input)

    # Step 2: Rate limit check
    rate_limiter.check_rate_limit(self.session_id)

    # Step 3: Build prompt
    prompt_result = self._prompt_builder.build(sanitized)

    # Step 4: Get conversation history
    history = self.memory.get_history()

    # Step 5: Call Gemini API
    response = self._client.generate(
        user_message=sanitized,
        system_prompt=prompt_result.system_prompt,
        chat_history=history,
    )

    # Step 6: Update memory
    self.memory.add_user_message(sanitized)
    self.memory.add_model_message(response)
    return response
```

---

## Security: The Hard Part

Finance is a high-stakes domain. A prompt injection attack could trick the bot into giving specific investment advice — which could mean real liability. I built **three layers of defense**:

### 1. Prompt Injection Defense

The security module uses regex patterns to detect common injection attempts:

```python
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts)"),
    re.compile(r"you\s+are\s+now\s+(?:a|an)\s+"),
    re.compile(r"act\s+as\s+(?:a|an)\s+"),
    re.compile(r"override\s+(your\s+)?(rules|instructions|prompt)"),
    re.compile(r"\[SYSTEM\]"),
    # ... and more
]
```

If any pattern matches, the request is rejected immediately — before it ever reaches the API.

### 2. Input Sanitization

Every input goes through a sanitization pipeline:
- Strip whitespace and control characters
- Limit input to 2,000 characters (prevents token bombing)
- Pattern matching against known injection vectors

### 3. Rate Limiting

A sliding window rate limiter tracks requests per session. Default limit: 10 requests per minute. This prevents both API cost abuse and brute-force injection attempts.

---

## Token-Aware Conversation Memory

LLMs have context windows, and API calls are billed per token. The memory system tracks conversation history while staying within a configurable token budget (default: 4,000 tokens).

When the budget is exceeded, the **oldest turns are trimmed first** — keeping recent context fresh while preventing runaway costs. The system also limits the maximum number of turns (default: 20) as an additional safeguard.

---

## Production API Client

The Gemini client wraps the Google GenAI SDK with production concerns:

- **Retry with exponential backoff** — 3 attempts with wait times from 2s to 30s, powered by the `tenacity` library
- **Token usage logging** — monitors prompt, response, and total tokens per call for cost tracking
- **Quota handling** — detects HTTP 429 / `RESOURCE_EXHAUSTED` errors and shows user-friendly recovery messages
- **Safety fallbacks** — gracefully handles empty responses and safety-blocked content

---

## Deployment

The project supports two deployment paths:

### Docker (Recommended)

```bash
docker-compose up -d      # Start
docker-compose logs -f    # View logs
docker-compose down       # Stop
```

The Dockerfile uses a non-root user and includes health checks.

### AWS EC2

Full deployment guide included:
- Ubuntu 22.04 LTS on a t3.small instance
- Nginx reverse proxy with WebSocket support
- systemd service for auto-restart on failures
- Ready for Let's Encrypt SSL/TLS

---

## Production Checklist

| Category | Feature | ✓ |
|---|---|---|
| Security | API key in .env (not hardcoded) | ✅ |
| Security | Prompt injection defense | ✅ |
| Security | Input sanitization & rate limiting | ✅ |
| Reliability | API retry with exponential backoff | ✅ |
| Reliability | Graceful error handling & health checks | ✅ |
| Observability | Structured logging & token tracking | ✅ |
| Performance | Token-aware memory trimming | ✅ |
| Testing | Unit tests with mocked API calls | ✅ |
| Deployment | Docker + EC2 with systemd | ✅ |

---

## Key Takeaways

1. **Security first in finance.** Prompt injection defense isn't optional — one bypassed guardrail could expose you to real liability.

2. **Memory management is underrated.** Token-aware trimming keeps conversations coherent without blowing up costs.

3. **Layered architecture pays off.** Separating UI → Service → API made testing trivial and changes low-risk.

4. **Domain prompts > generic prompts.** Topic-specific system instructions dramatically improve response quality for finance.

---

## What's Next

- **Redis** for persistent session memory across restarts
- **RAG integration** with a financial knowledge base
- **FastAPI backend** for REST API access
- **CI/CD** pipeline with GitHub Actions
- **Monitoring** with Prometheus + Grafana

---

## Try It Yourself

The full source code is open source and ready to deploy:

🔗 **GitHub:** [github.com/jakkojuraj-a11y/financial-advisor-chatbot](https://github.com/jakkojuraj-a11y/financial-advisor-chatbot)

Clone it, add your Gemini API key, and run `streamlit run app/main.py` — you'll have a working financial advisor chatbot in under 2 minutes.

---

*Built by [jakkojuraj-a11y](https://github.com/jakkojuraj-a11y) · February 2026*

*If you found this helpful, give it a ⭐ on GitHub and a 👏 here on Medium!*
