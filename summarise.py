# generate_summarized_context.py (v7.0 - Context-Aware Choices & Enhanced Template Discovery)
import ast
import os
import re
from pathlib import Path
from datetime import datetime

# --- CONFIGURATION (Unchanged) ---
PROJECT_ROOT = Path(__file__).parent
KEY_FILES_FULL = [
    "river/urls.py",
    "core/urls.py",
]
FILES_TO_SUMMARIZE = {
    "river/settings.py": "settings",
    "core/admin.py": "views_and_forms",
    "core/models.py": "models",
    "core/views.py": "views_and_forms",
    "core/forms.py": "views_and_forms",
    "river/core/tests.py": "tests",
}
OUTPUT_DIR = PROJECT_ROOT / "product" / "context"
OUTPUT_FILE = OUTPUT_DIR / "CURRENT_STATE.md"
IGNORE_DIRS = {"__pycache__", ".venv", "venv", ".git", "migrations", "static", "media"}

# --- HELPER FUNCTIONS (Unchanged) ---

def generate_tree_structure(root_dir, ignore_dirs):
    tree_lines = []
    root_dir = Path(root_dir)
    for path in sorted(root_dir.rglob('*')):
        if any(part in ignore_dirs for part in path.parts) or path.name == OUTPUT_FILE.name:
            continue
        depth = len(path.relative_to(root_dir).parts) - 1
        indent = '    ' * depth + '└── '
        tree_lines.append(f"{indent}{path.name}")
    return "\n".join(tree_lines)


def summarize_settings(file_path):
    summary = []
    important_settings = {
        "INSTALLED_APPS", "MIDDLEWARE", "DATABASES", "ROOT_URLCONF",
        "MEDIA_ROOT", "MEDIA_URL", "STATIC_URL", "CELERY_BROKER_URL"
    }
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line and line.strip() and line.strip()[0].isupper():
                var_name = line.split("=")[0].strip()
                if var_name in important_settings or not var_name.startswith(('AUTH', 'SECRET', 'LANGUAGE', 'TIME', 'DEFAULT')):
                    summary.append(line.strip())
    return "\n".join(summary)


# --- >>> FIXED & ENHANCED FUNCTION (Requirement #1) <<< ---
def summarize_models(file_path):
    """
    Summarizes Django models from a file with context-aware choices resolution.
    - Extracts class and field definitions.
    - For fields with 'choices', it first searches for a nested Choices class
      within the model before falling back to a global search in the file.
    """
    summary = []
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=file_path)

    def get_choices_from_class_node(class_node):
        """Helper to extract member names from a Choices class AST node."""
        members = []
        for item in class_node.body:
            if isinstance(item, ast.Assign) and len(item.targets) == 1 and isinstance(item.targets[0], ast.Name):
                members.append(item.targets[0].id)
        return members

    # Process each top-level node to find models
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            is_model = any(
                (isinstance(b, ast.Attribute) and b.attr == 'Model') or
                (isinstance(b, ast.Name) and b.id == 'Model')
                for b in node.bases
            )
            if not is_model:
                continue

            summary.append(f"class {node.name}(models.Model):")
            for item in node.body:
                if isinstance(item, ast.Assign) and len(item.targets) == 1 and isinstance(item.targets[0], ast.Name):
                    field_name = item.targets[0].id
                    field_type_str = ast.unparse(item.value)
                    summary.append(f"    {field_name} = {field_type_str}")

                    # Check for 'choices' keyword in the field's ast.Call
                    choices_class_name = None
                    if isinstance(item.value, ast.Call):
                        for kw in item.value.keywords:
                            if kw.arg == 'choices' and isinstance(kw.value, ast.Attribute) and isinstance(kw.value.value, ast.Name):
                                choices_class_name = kw.value.value.id
                                break
                    
                    if not choices_class_name:
                        continue

                    # --- Context-Aware Resolution Logic ---
                    found_choices = []
                    # 1. Local Search (Priority #1): Look for a nested class inside the model
                    for nested_item in node.body:
                        if isinstance(nested_item, ast.ClassDef) and nested_item.name == choices_class_name:
                            found_choices = get_choices_from_class_node(nested_item)
                            break
                    
                    # 2. Global Search (Fallback): If not found locally, search top-level classes
                    if not found_choices:
                        for top_level_node in tree.body:
                            if isinstance(top_level_node, ast.ClassDef) and top_level_node.name == choices_class_name:
                                found_choices = get_choices_from_class_node(top_level_node)
                                break
                    
                    if found_choices:
                        summary.append(f"    # Choices: {', '.join(found_choices)}")

            summary.append("")
    return "\n".join(summary)


# --- >>> ENHANCED FUNCTION (Requirement #2) <<< ---
def summarize_views_and_forms(file_path):
    """
    Intelligently summarizes Python files.
    - Extracts function/class signatures and docstrings.
    - Finds special developer comments (TODO, REFACTOR).
    - For Django ModelForms, it finds the associated model from the inner Meta class.
    - For Django views, it finds all possible templates from render() calls and `template_name` attributes.
    """
    summary = []
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    developer_notes = re.findall(r'#\s*(TODO|FIXME|NOTE|HACK|REFACTOR):(.*)', content, re.IGNORECASE)
    if developer_notes:
        summary.append("# --- Developer Notes ---")
        for note_type, note_text in developer_notes:
            summary.append(f"# {note_type.upper().strip()}: {note_text.strip()}")
        summary.append("# -----------------------\n")

    tree = ast.parse(content, filename=file_path)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            continue
        # We only want to process top-level definitions, not inner classes like Meta
        if node.col_offset > 0:
            continue

        signature_base = ast.unparse(node).split(':', 1)[0]
        comments = [] # To hold all generated comments for this line

        # --- Enhanced Template Discovery Logic ---
        found_templates = set()
        
        # A) For Function-Based Views & CBV Methods: find all render() calls
        for sub_node in ast.walk(node):
            if isinstance(sub_node, ast.Return) and isinstance(sub_node.value, ast.Call):
                call_node = sub_node.value
                func_name_str = ast.unparse(call_node.func)
                if 'render' in func_name_str and len(call_node.args) >= 2:
                    template_arg = call_node.args[1]
                    template_name = None
                    if isinstance(template_arg, ast.Constant): # Python 3.8+
                        template_name = template_arg.value
                    elif isinstance(template_arg, ast.Str):     # Older Python
                        template_name = template_arg.s
                    if template_name:
                        found_templates.add(template_name)

        # B) For Class-Based Views: find `template_name` attribute
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if (isinstance(item, ast.Assign) and len(item.targets) == 1 and
                    isinstance(item.targets[0], ast.Name) and item.targets[0].id == 'template_name'):
                    value_node = item.value
                    template_name = None
                    if isinstance(value_node, ast.Constant):
                        template_name = value_node.value
                    elif isinstance(value_node, ast.Str):
                        template_name = value_node.s
                    if template_name:
                        found_templates.add(template_name)

        if found_templates:
            comments.append(f"# Renders: {', '.join(sorted(list(found_templates)))}")

        # --- Existing Logic: Find model for ModelForms ---
        if isinstance(node, ast.ClassDef):
            model_name = None
            is_model_form = any(
                (isinstance(b, ast.Attribute) and b.attr == 'ModelForm') or
                (isinstance(b, ast.Name) and b.id == 'ModelForm')
                for b in node.bases
            )
            if is_model_form:
                for item in node.body:
                    if isinstance(item, ast.ClassDef) and item.name == 'Meta':
                        for meta_item in item.body:
                            if (isinstance(meta_item, ast.Assign) and
                                len(meta_item.targets) == 1 and
                                isinstance(meta_item.targets[0], ast.Name) and
                                meta_item.targets[0].id == 'model'):
                                model_name = ast.unparse(meta_item.value)
                                break
                        break
            if model_name:
                comments.append(f"# Binds to model: {model_name}")

        # --- Assemble final signature line ---
        final_signature = f"{ast.unparse(node).split(':', 1)[0]}:"
        if comments:
            final_signature += f"  {' '.join(comments)}"

        summary.append(final_signature)
        
        docstring = ast.get_docstring(node)
        if docstring:
            summary.append(f'    """{docstring.strip()}"""')
        summary.append("    # ... implementation hidden ...\n")

    return "\n".join(summary)


def summarize_tests(file_path):
    summary = []
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=file_path)
    summary.append(f"# Test Coverage Summary for {file_path.name}\n")
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            summary.append(f"class {node.name}:")
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name.startswith('test_'):
                    summary.append(f"    - def {item.name}(self):")
            summary.append("")
    if not any(line.strip().startswith('class') for line in summary):
        return "# No test classes found in this file."
    return "\n".join(summary)


# --- MAIN SCRIPT (Unchanged) ---

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    f.write("### File Structure\n```\n")
    f.write(f".\n{generate_tree_structure(PROJECT_ROOT, IGNORE_DIRS)}\n")
    f.write("```\n\n")

    f.write("### Summarized Key Files\n")
    for file, summary_type in sorted(FILES_TO_SUMMARIZE.items()):
        path = PROJECT_ROOT / file
        if path.exists():
            f.write(f"#### `SUMMARY: {file}`\n```python\n")
            if summary_type == "models":
                f.write(summarize_models(path))
            elif summary_type == "views_and_forms":
                f.write(summarize_views_and_forms(path))
            elif summary_type == "settings":
                f.write(summarize_settings(path))
            elif summary_type == "tests":
                f.write(summarize_tests(path))
            f.write("```\n\n")

    f.write("### Full Content of Critical Files\n")
    for file in sorted(KEY_FILES_FULL):
        path = PROJECT_ROOT / file
        if path.exists():
            f.write(f"#### `FULL: {file}`\n```python\n")
            f.write(path.read_text(encoding="utf-8"))
            f.write("\n```\n\n")

print(f"Summarized context file '{OUTPUT_FILE.relative_to(PROJECT_ROOT)}' generated successfully.")