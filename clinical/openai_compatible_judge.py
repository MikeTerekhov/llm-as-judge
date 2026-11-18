"""Optional OpenAI-compatible HTTP transport. Explicit opt-in only.

Never send patient data. Only use synthetic, non-sensitive research excerpts.
"""
import json
from urllib.parse import urlparse
from urllib.request import Request, urlopen

MAX_RESPONSE = 8192

def make_chat_transport(*, endpoint: str, model: str, api_key: str, timeout: int = 15):
    parsed = urlparse(endpoint)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or
            parsed.password or parsed.fragment or parsed.query):
        raise ValueError("Model endpoint must be an explicit HTTPS URL")
    if not model.strip() or not api_key.strip() or not 1 <= timeout <= 60:
        raise ValueError("Invalid model transport configuration")
    def call(prompt: str) -> str:
        body = json.dumps({"model": model, "temperature": 0,
                           "messages": [{"role": "system", "content": "Return only structured JSON. Never provide clinical advice."},
                                        {"role": "user", "content": prompt}]}).encode("utf-8")
        request = Request(endpoint, data=body, method="POST",
                          headers={"Authorization": "Bearer " + api_key,
                                   "Content-Type": "application/json"})
        with urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise ValueError("Model endpoint failed")
            data = response.read(MAX_RESPONSE + 1)
        if len(data) > MAX_RESPONSE:
            raise ValueError("Model response too large")
        result = json.loads(data)
        return result["choices"][0]["message"]["content"]
    return call
