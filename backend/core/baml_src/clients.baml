
client<llm> OpenGemini2Pro {
  provider openai-generic
  options {
    base_url "https://openrouter.ai/api/v1"
    api_key env.OPENROUTER_API_KEY
    model "google/gemini-2.0-pro-exp-02-05:free"
  }
}

client<llm> OpenGemini2Flash {
  provider openai-generic
  options {
    base_url "https://openrouter.ai/api/v1"
    api_key env.OPENROUTER_API_KEY
    model "google/gemini-2.0-flash-exp:free"
  }
}


client<llm> OpenGemini2FlashThinking {
  provider openai-generic
  options {
    base_url "https://openrouter.ai/api/v1"
    api_key env.OPENROUTER_API_KEY
    model "google/gemini-2.0-flash-thinking-exp:free"
  }
}



client<llm> GoogleGemini2Pro {
  provider google-ai
  options {
    base_url "https://generativelanguage.googleapis.com/v1beta"
    api_key env.GOOGLE_API_KEY
    model "gemini-2.0-pro-exp-02-05"
  }
}

client<llm> GoogleGemini2Flash {
  provider google-ai
  options {
    base_url "https://generativelanguage.googleapis.com/v1beta"
    api_key env.GOOGLE_API_KEY
    model "gemini-2.0-flash"
  }
}

client<llm> GoogleGemini2FlashThinking {
  provider google-ai
  options {
    base_url "https://generativelanguage.googleapis.com/v1beta"
    api_key env.GOOGLE_API_KEY
    model "gemini-2.0-flash-thinking-exp-01-21"
  }
}

client<llm> GroqLLM3370b {
  provider openai-generic
  options {
    base_url "https://api.groq.com/openai/v1"
    api_key env.GROQ_API_KEY
    model "llama-3.3-70b-versatile"
  }
}

client<llm> GroqLLM370b8192 {
  provider openai-generic
  options {
    base_url "https://api.groq.com/openai/v1"
    api_key env.GROQ_API_KEY
    model "llama3-70b-8192"
  }
}



client<llm> LLMclient {
  provider "openai-generic"
  options {
    base_url "http://localhost:11434/v1"

    model "deepseek-r1:8b"
    temperature 0.0
  }
}



// https://docs.boundaryml.com/docs/snippets/clients/fallback
client<llm> LLMFallback {
  provider fallback
  retry_policy Exponential
  options {
    // This will try the clients in order until one succeeds
    strategy [GoogleGemini2Pro, OpenGemini2Pro, GoogleGemini2FlashThinking, OpenGemini2FlashThinking,  GroqLLM3370b, GroqLLM370b8192]
  }
}

// https://docs.boundaryml.com/docs/snippets/clients/retry
retry_policy Constant {
  max_retries 3
  // Strategy is optional
  strategy {
    type constant_delay
    delay_ms 200
  }
}

retry_policy Exponential {
  max_retries 2
  // Strategy is optional
  strategy {
    type exponential_backoff
    delay_ms 300
    multiplier 1.5
    max_delay_ms 10000
  }
}