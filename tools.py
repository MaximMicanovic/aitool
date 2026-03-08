"""Tool definitions and handlers for the ai CLI."""

import json
import re
import subprocess
import sys
import urllib.request

# Commands that are safe to run without confirmation even via the bash tool
SAFE_COMMAND_PREFIXES = (
    "head ",
    "tail ",
    "less ",
    "more ",
    "ls ",
    "ls\n",
    "ll ",
    "tree ",
    "find ",
    "grep ",
    "rg ",
    "ag ",
    "awk ",
    "sed -n",
    "git log",
    "git status",
    "git diff",
    "git show",
    "git branch",
    "ps ",
    "ps\n",
    "df ",
    "du ",
    "top ",
    "htop",
    "env",
    "echo ",
    "pwd",
    "which ",
    "whereis ",
    "file ",
    "wc ",
    "sort ",
    "uniq ",
    "cut ",
    "tr ",
    "curl -s",
    "curl --silent",
    "wget -q",
    "python3 -c",
    "python -c",
    "node -e",
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bash_read",
            "description": (
                "Run a read-only bash command that does NOT modify any files or system state. "
                "Use for reading files (cat, head, tail), listing directories (ls, find, tree), "
                "searching (grep, rg), checking status (git status, git log, ps, df, du), "
                "printing environment (env, echo, pwd), etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The read-only bash command to run",
                    }
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web using DuckDuckGo and return a summary of results. "
                "Use this to look up current information, documentation, errors, or anything online."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": (
                "Run a bash command that may modify files or system state. "
                "Use for writing/editing/deleting files, creating directories, "
                "installing packages, running scripts, git commits, etc. "
                "The user will be asked to confirm before the command runs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The bash command to run",
                    }
                },
                "required": ["command"],
            },
        },
    },
]


def web_search(query):
    """Search DuckDuckGo and return text results."""
    import urllib.parse

    url = (
        "https://api.duckduckgo.com/?q="
        + urllib.parse.quote(query)
        + "&format=json&no_html=1&skip_disambig=1"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ai-cli/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        results = []
        if data.get("AbstractText"):
            results.append(f"Summary: {data['AbstractText']}")
            if data.get("AbstractURL"):
                results.append(f"Source: {data['AbstractURL']}")

        for item in data.get("RelatedTopics", [])[:5]:
            if isinstance(item, dict) and item.get("Text"):
                results.append(f"- {item['Text']}")
                if item.get("FirstURL"):
                    results.append(f"  {item['FirstURL']}")

        if not results:
            return f"No results found for: {query}"
        return "\n".join(results)
    except Exception as e:
        return f"[Search error: {e}]"


def _is_cat_command(command_part):
    """Return True when a command segment starts with the cat command."""
    return bool(re.match(r"^cat(?:\s|$)", command_part))


def _has_output_redirection(command_part):
    """Detect shell output redirection operators in a command segment."""
    import shlex

    try:
        lexer = shlex.shlex(command_part, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        # If parsing fails, play it safe and require confirmation.
        return True

    for token in tokens:
        if token and set(token) <= set("<>|&") and ">" in token:
            return True
    return False


def _is_safe_command(command):
    # Tokenize with shlex so | inside quoted strings isn't treated as a pipe
    import shlex

    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return False

    # Split token stream into segments on shell control operators
    segments = []
    current = []
    for tok in tokens:
        if tok in ("&&", "||", "|", ";"):
            segments.append(" ".join(current))
            current = []
        else:
            current.append(tok)
    segments.append(" ".join(current))

    for part in segments:
        part = part.strip()
        if not part:
            continue

        if _is_cat_command(part):
            if _has_output_redirection(part):
                return False
            continue

        if any(part.startswith(p) for p in SAFE_COMMAND_PREFIXES) or part.startswith(
            "cd "
        ):
            continue

        return False

    return True


def run_bash(command, confirm=False, c=lambda _color, text: text):
    if confirm and _is_safe_command(command):
        confirm = False  # auto-approve read-only commands
    if confirm:
        print(c("yellow", "\nCommand to run:"))
        print(c("bold", f"  {command}"))
        try:
            answer = input(c("yellow", "Run? [Y/n] ")).strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            return "[Cancelled by user]"
        if answer in ("n", "no"):
            return "[Command cancelled by user]"

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout
        if result.stderr:
            output += result.stderr if not output else f"\n[stderr]:\n{result.stderr}"
        if result.returncode != 0:
            output += f"\n[exit code {result.returncode}]"
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "[Timed out after 60 seconds]"
    except Exception as e:
        return f"[Error: {e}]"


def handle_tool_call(tool_call, c=lambda _color, text: text):
    name = tool_call["function"]["name"]
    args = tool_call["function"].get("arguments", {})
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except Exception:
            args = {}
    command = args.get("command", "")

    if name == "bash_read":
        print(c("dim", "  [read] ") + c("bold", command))
        result = run_bash(command, confirm=not _is_safe_command(command), c=c)
    elif name == "bash":
        result = run_bash(command, confirm=True, c=c)
    elif name == "web_search":
        query = args.get("query", "")
        print(c("dim", "  [search] ") + c("bold", query))
        result = web_search(query)
    else:
        result = f"[Unknown tool: {name}]"

    cancelled = result == "[Command cancelled by user]"
    lines = result.splitlines()
    preview = "\n".join(f"  {l}" for l in lines[:20])
    if len(lines) > 20:
        preview += f"\n  ... ({len(lines) - 20} more lines)"
    print(c("dim", preview))
    print()
    return result, cancelled
