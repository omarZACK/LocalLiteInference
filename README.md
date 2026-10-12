# Local LLM Gateway (LiteLLM + Docker)

A lightweight, self-hosted AI routing layer packaged in Docker. This project provides a unified, OpenAI-compatible proxy interface to access and orchestrate local models hosted on **Ollama** or custom **Hugging Face** runtimes—all running locally on your hardware.

## Highlights

- **Unified OpenAI-Compatible API**: Expose standard `/v1/chat/completions` endpoints to integrate seamlessly with tools like Open WebUI, Cursor, Continue, LangChain, or CrewAI.
- **Multi-Backend Orchestration**: Route requests seamlessly between local Ollama instances and Hugging Face pipelines without code-level changes.
- **Dockerized & Isolated**: Run LiteLLM Proxy in an isolated container while securely bridging traffic to host-level GPU inference engines.
- **Dynamic Model Fallbacks & Routing**: Configure load balancing, rate limiting, and fallback strategies across multiple local weights.
- **Zero Cloud Leakage**: Keep inference data, prompts, and completions strictly on your local machine.

## Architecture

                 ┌────────────────────────┐
                 │ Client App / Agent / UI │
                 └───────────┬────────────┘
                             │ (OpenAI API / Port 4000)
                             ▼
         ┌───────────────────────────────────────┐
         │       LiteLLM Proxy (Docker)          │
         │  - Route handling & auth              │
         │  - Formatting & schema adaptation     │
         └───────┬───────────────────────┬───────┘
                 │                       │
                 ▼                       ▼
    ┌─────────────────────────┐  ┌─────────────────────────┐
    │      Local Ollama       │  │  Hugging Face Runtime   │
    │  (e.g., Qwen, Llama 3)  │  │  (TGI / vLLM / Local)   │
    └─────────────────────────┘  └─────────────────────────┘
