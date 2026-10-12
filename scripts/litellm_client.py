import os
import sys
import argparse
import time
from pathlib import Path
from dotenv import load_dotenv
import json
import requests


def is_running_in_docker() -> bool:
    """Check whether execution is inside a Docker container."""
    return Path("/.dockerenv").exists() or Path("/run/.containerenv").exists()


def load_env():
    """Load environment variables and return the LiteLLM proxy base URL and master key."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)

    if is_running_in_docker():
        default_url = "http://litellm-proxy:4000"
    else:
        port = os.getenv("LITELLM_PORT", "4001")
        default_url = f"http://localhost:{port}"

    base_url = os.getenv("LITELLM_PROXY_URL", default_url)
    master_key = os.getenv("LITELLM_MASTER_KEY") or os.getenv("LITELLM_TOKEN", "")
    return base_url, master_key


def _get_headers(api_key: str) -> dict:
    """Construct request authorization headers."""
    return {"Authorization": f"Bearer {api_key}"} if api_key else {}


def stream_chat_completion(model: str = "coding-fast", content: str = "Write a short poem about Linux terminal."):
    """Streaming chat completion with live token generation metrics."""
    api_base, api_key = load_env()
    url = f"{api_base}/v1/chat/completions"
    headers = _get_headers(api_key)
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 512,
        "stream": True,
        "stream_options": {"include_usage": True},
    }

    start_time = time.perf_counter()
    first_token_time = None
    accumulated_content = []
    completion_tokens = 0
    prompt_tokens = 0

    response = requests.post(url, json=payload, headers=headers, stream=True)
    response.raise_for_status()

    print("\n" + "=" * 25 + " LIVE STREAM " + "=" * 25)
    for line in response.iter_lines():
        if not line:
            continue
        try:
            data = line.decode("utf-8")
            if data.startswith("data: "):
                data = data[6:]
            if data.strip() == "[DONE]":
                break

            chunk = json.loads(data)

            # Check if this chunk delivers token usage stats
            if "usage" in chunk and chunk["usage"]:
                completion_tokens = chunk["usage"].get("completion_tokens", completion_tokens)
                prompt_tokens = chunk["usage"].get("prompt_tokens", prompt_tokens)

            choices = chunk.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {}).get("content", "")
                if delta:
                    if first_token_time is None:
                        first_token_time = time.perf_counter()
                    accumulated_content.append(delta)
                    print(delta, end="", flush=True)
        except Exception:
            continue

    end_time = time.perf_counter()
    print("\n" + "=" * 63 + "\n")

    # Fallback approximation (~4 chars/token) if backend didn't send usage metadata
    if completion_tokens == 0:
        total_text = "".join(accumulated_content)
        completion_tokens = max(1, len(total_text) // 4)

    total_latency = end_time - start_time
    ttft = (first_token_time - start_time) if first_token_time else total_latency
    gen_time = max(0.0001, end_time - (first_token_time or start_time))
    tokens_per_sec = completion_tokens / gen_time

    print("⚡ Performance Metrics:")
    print(f" • Completion tokens: {completion_tokens} tokens")
    if prompt_tokens:
        print(f" • Prompt tokens:     {prompt_tokens} tokens")
    print(f" • Time to 1st token: {ttft:.3f} s")
    print(f" • Generation time:   {gen_time:.3f} s")
    print(f" • Generation speed:  {tokens_per_sec:.2f} tokens/s")
    print(f" • Total latency:     {total_latency:.3f} s\n")


def chat_completion(model: str = "coding-fast", content: str = "Hello, how are you?"):
    """Non-streaming chat completion with token speed metrics."""
    api_base, api_key = load_env()
    url = f"{api_base}/v1/chat/completions"
    headers = _get_headers(api_key)
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 512,
    }

    start_time = time.perf_counter()
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    end_time = time.perf_counter()

    data = response.json()
    main_content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

    print("Response content:")
    print(main_content)

    if "reasoning_content" in data:
        print("\nReasoning content:")
        print(data["reasoning_content"])

    # Calculate token metrics
    total_latency = max(0.0001, end_time - start_time)
    usage = data.get("usage", {})
    completion_tokens = usage.get("completion_tokens")

    # Fallback approximation if usage is omitted
    if not completion_tokens:
        completion_tokens = max(1, len(main_content) // 4)

    tokens_per_sec = completion_tokens / total_latency

    print("\n" + "-" * 35)
    print("⚡ Performance Metrics:")
    print(f" • Completion tokens: {completion_tokens} tokens")
    if "prompt_tokens" in usage:
        print(f" • Prompt tokens:     {usage['prompt_tokens']} tokens")
    print(f" • Total latency:     {total_latency:.3f} s")
    print(f" • Generation speed:  {tokens_per_sec:.2f} tokens/s")
    print("-" * 35 + "\n")

    return data


def main():
    parser = argparse.ArgumentParser(description="LiteLLM client with dynamic model routing")
    parser.add_argument(
        "--model",
        default="coding-fast",
        help="Model identifier (alias or explicit model name).",
    )
    parser.add_argument(
        "--prompt",
        default="Write a short poem about Linux terminal.",
        help="Prompt to send to the model.",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Use streaming mode instead of a single response.",
    )
    args = parser.parse_args()

    if args.stream:
        stream_chat_completion(args.model, args.prompt)
    else:
        chat_completion(args.model, args.prompt)


if __name__ == "__main__":
    main()