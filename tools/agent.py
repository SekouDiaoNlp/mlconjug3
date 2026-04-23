import os
import sys
import subprocess
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are a senior Python + NLP engineer working inside a developer CLI.

Rules:
- Be concise
- Prefer diffs or patch-style output
- If code is unclear, ask for clarification
"""

def get_git_context():
    try:
        status = subprocess.check_output(["git", "status"], text=True)
        diff = subprocess.check_output(["git", "diff"], text=True)
        return f"STATUS:\n{status}\n\nDIFF:\n{diff}"
    except Exception:
        return "Not a git repository."

def run_agent(task: str):
    resp = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""
TASK:
{task}

CONTEXT:
{get_git_context()}
"""
            },
        ],
    )

    print(resp.output_text)


def main():
    task = " ".join(sys.argv[1:])
    if not task:
        print('Usage: codex "your request"')
        return

    run_agent(task)


if __name__ == "__main__":
    main()
