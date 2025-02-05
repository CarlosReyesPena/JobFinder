// Learn more about clients at https://docs.boundaryml.com/docs/snippets/clients/overview

client<llm> Ollama {
  provider "openai-generic"
  options {
    base_url "http://localhost:11434/v1"
    model "deepseek-r1:8b"
  }
}

