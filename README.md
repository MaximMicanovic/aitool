# ai

An interactive terminal chat tool powered by [Ollama](https://ollama.com). Talks to locally running models, streams responses in real time, and can read and edit files on your machine using bash tools.

## Features

- Streaming output — see the response as it generates
- Tool calling — the AI can run bash commands to read and edit files
- Confirmation prompt before any command that changes files
- Working directory awareness — knows where you launched it from
- `<think>` block filtering for reasoning models (qwen3, etc.)
- No external dependencies — only Python stdlib

## Requirements

- Python 3.7+
- [Ollama](https://ollama.com) running locally (`ollama serve`)
- A model that supports tool calling (see below)

## Installation

```bash
# Clone or copy the repo
git clone <your-repo-url> ~/python/ai

# Add to PATH (add this to your ~/.zshrc or ~/.bashrc)
export PATH="$HOME/python/ai:$PATH"

# Reload your shell
source ~/.zshrc
```

## Recommended Models

Not all models support tool calling. These work well:

| Model | Size | Notes |
|---|---|---|
| `qwen3:4b` | 4B | Good balance of speed and quality |
| `qwen3:14b` | 14B | Better reasoning, slower |
| `qwen3.5:9b-q8_0` | 9B | High quality quantized |

```bash
ollama pull qwen3:4b
```

## Usage

```bash
# Start with auto-selected model
ai

# Use a specific model
ai -m qwen3:4b

# Set a system prompt / persona
ai -s "You are a senior Python developer"

# List available models
ai --list

# Disable streaming (wait for full response)
ai --no-stream
```

### Environment Variables

```bash
export OLLAMA_MODEL="qwen3:4b"         # default model
export OLLAMA_HOST="http://localhost:11434"  # ollama URL (default)
export OLLAMA_SYSTEM="You are a Linux expert"  # default system prompt
```

## In-Chat Commands

| Command | Description |
|---|---|
| `/model [name]` | Show current model or switch to another |
| `/system [text]` | Show or update the system prompt |
| `/clear` | Clear conversation history |
| `/history` | Print the full conversation so far |
| `/help` | Show this list |
| `/exit` | Quit |

## Tools

The AI has access to two bash tools:

### `bash_read`
Runs read-only commands automatically, without asking. Used for things like listing files, reading file contents, searching with grep, checking git status, etc.

```
  [read] ls -la
  total 32
  drwxr-xr-x  3 maxim maxim 4096 ...
  ...
```

### `bash`
Runs commands that modify files or system state. Always shows the command and asks for confirmation before running.

```
Command to run:
  sed -i 's/old/new/' main.py
Run? [y/N]
```

## Working Directory

The AI is told your current working directory when it starts. Run it from inside your project and it will use relative paths correctly:

```bash
cd ~/projects/myapp
ai -m qwen3:4b
# AI knows it's working in ~/projects/myapp
```

## Example Session

```
ai [qwen3:4b] /home/maxim/projects/myapp

You: what python files are in this project?

  [read] find . -name "*.py"
  ./main.py
  ./utils/helpers.py
  ./tests/test_main.py

AI: There are 3 Python files: main.py, a helpers module in utils/, and a test file.

You: there's a bug in main.py on line 12, can you fix it?

  [read] cat main.py
  ...

Command to run:
  sed -i '12s/old_function/new_function/' main.py
Run? [y/N] y

AI: Fixed. The call on line 12 now uses `new_function` instead of `old_function`.
```
