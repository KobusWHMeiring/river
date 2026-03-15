import json
import os
import subprocess
import sys
from pathlib import Path
from urllib import error, request


# Load .env manually to avoid 'python-dotenv' dependency for a simple linter
def load_env():
    env_path = Path(".env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.strip() and not line.startswith("#"):
                key, _, value = line.partition("=")
                os.environ[key.strip()] = value.split("#")[0].strip()

def call_kimi_api(prompt: str) -> str:
    """
    Surgical AI Audit: Calls Moonshot AI (Kimi) to verify code against Build Principles.
    """
    api_key = os.getenv("KIMI_API_KEY")
    model = os.getenv("KIMI_MODEL", "kimi-k2.5")

    if not api_key:
        return "ERROR: KIMI_API_KEY not found in .env"

    url = "https://api.moonshot.cn/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a brutal Staff Engineer auditing code against strict Build Principles."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1 # Keep it deterministic for linting
    }

    try:
        req = request.Request(url, data=json.dumps(data).encode(), headers=headers)
        with request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            return res_data["choices"][0]["message"]["content"]
    except error.HTTPError as e:
        return f"ERROR: Kimi API returned {e.code} - {e.reason}"
    except Exception as e:
        return f"ERROR: AI Linting failed - {str(e)}"

def call_gemini_api(prompt: str) -> str:
    """
    Surgical AI Audit: Calls Google Gemini API (flash 2.0) to verify code against Build Principles.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    if not api_key:
        return "ERROR: GEMINI_API_KEY not found in .env"

    # Gemini API uses a different endpoint structure:
    # https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "contents": [{
            "parts": [
                {"text": "You are a brutal Staff Engineer auditing code against strict Build Principles."},
                {"text": prompt}
            ]
        }],
        "generationConfig": {
            "temperature": 0.1
        }
    }

    try:
        req = request.Request(url, data=json.dumps(data).encode(), headers=headers)
        with request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            # Path to the response text in Gemini's response structure
            return res_data["candidates"][0]["content"]["parts"][0]["text"]
    except error.HTTPError as e:
        return f"ERROR: Gemini API returned {e.code} - {e.reason}"
    except Exception as e:
        return f"ERROR: AI Linting failed - {str(e)}"

def main():
    print("🔍 [River Project] Running AiLint on staged changes...")
    load_env()

    # 1. Get staged changes
    try:
        diff = subprocess.check_output(["git", "diff", "--cached"], text=True, encoding="utf-8")
        if not diff.strip():
            print("✅ No staged changes to lint. Run `git add .` first.")
            sys.exit(0)
    except subprocess.CalledProcessError:
        print("❌ Error reading git diff.")
        sys.exit(1)

    # 2. Load Build Principles
    principles_path = Path("product/context/build_principles.md")
    if not principles_path.exists():
        print(f"❌ Could not find {principles_path}")
        sys.exit(1)

    principles = principles_path.read_text(encoding="utf-8")

    # 3. Construct the prompt
    prompt = f"""
You are a brutal, highly-technical Staff Software Engineer at the "River Rehabilitation Project".
Your ONLY job is to compare the provided CODE DIFF against our BUILD PRINCIPLES.

### BUILD PRINCIPLES:
{principles}

### CRITICAL DISTINCTION - READ CAREFULLY:

**DO NOT FLAG THESE - THEY ARE CORRECT:**

1. **Model.clean() AND Form.clean() ARE VALIDATION - NEVER FLAG THESE:**
   - These are Django's standard validation hooks
   - They check data integrity (e.g., "date is required if not rolling")
   - They do NOT belong in services - they belong in models/forms
   - **IF YOU SEE A METHOD NAMED `clean(self)` IN A MODEL OR FORM - DO NOT FLAG IT EVER**
   - Example: `def clean(self): if not self.is_rolling and not self.date: raise ValidationError(...)` ✅ CORRECT - DO NOT FLAG

2. **Field Definitions and Widgets - NEVER FLAG THESE:**
   - Model fields: `todo_position = models.PositiveIntegerField(default=0)`
   - Form widgets: `widgets = {{'field': forms.TextInput(attrs=...)}}`
   - Meta classes, import statements, __str__ methods
   
3. **Type Hints in services/ ARE CORRECT - NEVER FLAG MISSING HINTS IF THEY EXIST:**
   - Example of CORRECT hints: `def move_todo_task(task_id: int, new_status: str, new_index: int) -> None:`
   - Only flag if hints are ACTUALLY missing, not if you can't see them in the diff

**ONLY FLAG THESE ACTUAL VIOLATIONS:**
- Workflow orchestration (e.g., creating related records, state machines)
- Data transformation beyond simple validation (e.g., calculating values, aggregating data)
- Multi-step operations that should be in services (e.g., "create task series and send notifications")
- Complex business rules that affect multiple models

### ADDITIONAL WHITELIST - DO NOT FLAG:
- **Import statements** (e.g., `from .services.task_services import move_todo_task`)
- **Metric calculations in views** (e.g., `total_weeds = metrics.filter(...).aggregate(...)`)
- **Proper exception handling** (e.g., `except Exception as e: return JsonResponse({{'error': str(e)}})`)
- **SortableJS for drag-and-drop** (lightweight library, acceptable per "Vanilla First" for complex interactions)
- **Context preservation via `next` parameter** in forms and redirects

### CRITICAL - READ THE DIFF CONTEXT CAREFULLY:
The line numbers in the diff are relative to the hunk, not absolute file positions. Lines starting with `+` are additions, `-` are removals. Make sure you understand the CONTEXT before flagging violations.

### INSTRUCTIONS:
1. Ignore standard syntax errors (Ruff handles that).
2. Focus strictly on ARCHITECTURAL VIOLATIONS:
   - SERVICE LAYER: Is business LOGIC (not validation) in `views.py` or `models.py` instead of `services/`?
   - SILENT ERRORS: Is there a bare `except: pass`?
   - TYPE HINTS: Are `services/` functions ACTUALLY missing hints (not just imports)?
   - VANILLA JS: Is there a heavy JS framework instead of Native DOM APIs?
   - CONTEXT: Are redirect parameters (`next`) being lost in navigation?
3. If code violates ANY principle, output: FILENAME, LINE NUMBER, and the BROKEN RULE.
4. If code adheres perfectly, output EXACTLY the word "PASS" and nothing else.

### CODE DIFF:
{diff}
"""

    # 4. Execute AI check
    print(f"📊 Diff Size: {len(diff)} characters")
    print("-" * 20 + " PROMPT START " + "-" * 20)
    print(prompt)
    print("-" * 20 + " PROMPT END " + "-" * 20)

    # Try Gemini first if key exists, then fallback to Kimi
    if os.getenv("GEMINI_API_KEY"):
        print(f"⏳ Waiting for {os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')} Audit...")
        result = call_gemini_api(prompt)
    else:
        print(f"⏳ Waiting for {os.getenv('KIMI_MODEL', 'kimi-k2.5')} Audit...")
        result = call_kimi_api(prompt)

    print("\n" + "="*40)
    if result.strip().upper() == "PASS":
        print("✅ AiLint PASSED. You may now `git commit`.")
        sys.exit(0)
    else:
        print("🚨 [River Project] POTENTIAL ARCHITECTURAL VIOLATIONS DETECTED:\n")
        print(result)
        print("\n" + "="*40)
        print("⚠️  IMPORTANT - REVIEW CAREFULLY:")
        print("   The AI may flag false positives for:")
        print("   • Model.clean() and Form.clean() methods (these are VALIDATION, not business logic)")
        print("   • Field definitions and widget configurations")
        print("   • Import statements")
        print("   • Type hints that ARE present")
        print("\n   If violations appear incorrect, review the actual code before fixing.")
        print("👉 If legitimate violations exist, feed them to your Dev AI before committing.")
        sys.exit(1)

if __name__ == "__main__":
    main()
