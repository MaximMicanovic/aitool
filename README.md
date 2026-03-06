# ai

An interactive terminal chat tool powered by [Ollama](https://ollama.com). Talks to locally running models, streams responses in real time, and can read files, run commands, and search the web using built-in tools.

## Features

- Streaming output — see the response as it generates
- Thinking spinner that clears cleanly before output begins
- Tool calling — the AI can run bash commands and search the web
- Read-only commands run automatically; write commands ask for confirmation
- Safe command whitelist — common read-only patterns never prompt
- Working directory awareness — knows where you launched it from
- Context save/load — resume sessions across restarts
- `<think>` block filtering for reasoning models
- Retry logic when the model produces no output
- No external dependencies — only Python stdlib

## Requirements

- Python 3.7+
- [Ollama](https://ollama.com) running locally (`ollama serve`)
- Any model that supports tool calling

## Installation

```bash
git clone https://github.com/MaximMicanovic/aitool ~/.local/aitool

# Add to PATH (add this to your ~/.zshrc or ~/.bashrc)
export PATH="$HOME/.local/aitool:$PATH"

source ~/.zshrc
```

## Recommended Models

Any Ollama model with tool calling support works. Some good options:

| Model | Size | Notes |
|---|---|---|
| `qwen3.5:9b-q8_0` | 9B | Default — strong reasoning and tool use |
| `qwen3:4b` | 4B | Faster, lighter |
| `llama3.1:8b` | 8B | Good general purpose |
| `mistral:7b` | 7B | Fast and capable |

```bash
ollama pull qwen3.5:9b-q8_0
```

## Usage

```bash
# Start with default model
ai

# Use a specific model
ai -m llama3.1:8b

# Set a system prompt
ai -s "You are a senior Python developer"

# Resume a previous session
ai -l ai-context.json

# List available models
ai --list

# Disable streaming
ai --no-stream
```

### Environment Variables

```bash
export OLLAMA_MODEL="llama3.1:8b"
export OLLAMA_HOST="http://localhost:11434"  # default
export OLLAMA_SYSTEM="You are a Linux expert"
```

## In-Chat Commands

| Command | Description |
|---|---|
| `/model [name]` | Show current model or switch to another |
| `/system [text]` | Show or update the system prompt |
| `/clear` | Clear conversation history |
| `/history` | Print the full conversation so far |
| `/save [file]` | Save session to file (default: `ai-context.json`) |
| `/load <file>` | Load a saved session |
| `/help` | Show this list |
| `/exit` | Quit |

## Tools

The AI has access to three tools:

### `bash_read`
Runs read-only commands automatically without asking — listing files, reading content, searching with grep, checking git status, etc. If a command looks non-read-only (for example `cat > file.txt`), it is treated as unsafe and asks for confirmation.

```
  [read] find . -name "*.py"
  ./main.py
  ./utils/helpers.py
```

### `bash`
Runs commands that modify files or system state. Shows the command and asks for confirmation first. Common read-only patterns (head, tail, grep, git log, etc.) are whitelisted and skip the prompt even if the model uses this tool. `cat` is auto-approved only for read usage (for example `cat file.txt`); `cat` with output redirection (for example `cat > file.txt`) requires confirmation.

```
Command to run:
  sed -i 's/old/new/' main.py
Run? [Y/n]
```

### `web_search`
Searches the web via DuckDuckGo and returns results. Runs automatically without confirmation.

```
  [search] Python subprocess timeout handling
  Summary: ...
```

## Working Directory

The AI is told your current working directory at startup. Launch it from inside your project and it will use relative paths correctly:

```bash
cd ~/projects/myapp
ai
# AI knows it's working in ~/projects/myapp
```

## Example Session

```
ai [qwen3.5:9b-q8_0] /home/user/projects/myapp

You: what python files are in this project?

  [read] find . -name "*.py"
  ./main.py
  ./utils/helpers.py
  ./tests/test_main.py

AI: There are 3 Python files: main.py, a helpers module in utils/, and a test file.

You: there's a bug in main.py on line 12, fix it

  [read] cat -n main.py

Command to run:
  sed -i '12s/old_function/new_function/' main.py
Run? [Y/n] y

AI: Fixed. Line 12 now calls `new_function` instead of `old_function`.
```
