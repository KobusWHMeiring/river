"""Python AST rules for architecture guard."""
import ast
from pathlib import Path

from ..rules import rule
from ..violation import Violation

SRC_ROOT = Path("src")


def _get_src_root() -> Path:
    """Resolve src/ at call time so tests can chdir."""
    return SRC_ROOT.resolve()
SKIP_DIRS = {"migrations", "tests", "management", "__pycache__"}


def _iter_py_files():
    """Yield all .py files in src/ excluding skipped dirs and test files."""
    for py_file in _get_src_root().rglob("*.py"):
        if any(skip in py_file.parts for skip in SKIP_DIRS):
            continue
        if "site-packages" in str(py_file):
            continue
        # Skip test files (Django TestCase wraps every test in a transaction)
        stem = py_file.stem
        if stem == "tests" or stem.startswith("test_") or stem.startswith("tests_") or stem == "conftest":
            continue
        yield py_file


def _is_in_views(filepath: Path) -> bool:
    return "views" in filepath.parts


def _is_in_services(filepath: Path) -> bool:
    return "services" in filepath.parts


def _has_transaction_atomic(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Check if function is decorated with or wraps code in transaction.atomic."""
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Attribute):
            if isinstance(decorator.value, ast.Name) and decorator.value.id == "transaction" and decorator.attr == "atomic":
                return True
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                if isinstance(decorator.func.value, ast.Name) and decorator.func.value.id == "transaction" and decorator.func.attr == "atomic":
                    return True
    for child in ast.walk(node):
        if isinstance(child, ast.With):
            for item in child.items:
                if isinstance(item.context_expr, ast.Call):
                    ce = item.context_expr
                    if isinstance(ce.func, ast.Attribute):
                        if isinstance(ce.func.value, ast.Name) and ce.func.value.id == "transaction" and ce.func.attr == "atomic":
                            return True
    return False


def _classify_file_domain(filepath: Path) -> str | None:
    """Extract domain name from a service or model file path."""
    name = filepath.stem
    for suffix in ("_service", "_services"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def _relpath(path: Path) -> str:
    """Return path relative to CWD, or just the path string."""
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


@rule("RU-001", severity="ERROR", category="python")
def check_silenced_exceptions():
    """Detect except blocks that silently swallow exceptions."""
    violations = []
    for py_file in _iter_py_files():
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                body_stripped = [
                    stmt
                    for stmt in node.body
                    if not (
                        isinstance(stmt, ast.Expr)
                        and isinstance(stmt.value, ast.Constant)
                    )
                    and not isinstance(stmt, ast.Pass)
                ]
                if len(body_stripped) == 0:
                    violations.append(
                        Violation(
                            rule_id="RU-001",
                            severity="ERROR",
                            category="python",
                            file=_relpath(py_file),
                            line=node.lineno,
                            message="Silenced exception: except block has no action (no re-raise, no log, no error handling).",
                            snippet=f"except {ast.unparse(node.type) if node.type else ''}:",
                        )
                    )
    return violations


def _has_setattr_in_enclosing_function(save_node: ast.Call, tree: ast.AST) -> bool:
    """Check if the enclosing function of a .save() call contains setattr() calls.
    
    This detects the generic PATCH pattern where views loop over fields
    and set them via setattr() before calling .save() — equivalent to DRF's
    serializer.update() behaviour.
    """
    parent_map = _build_parent_map(tree)
    # Walk up from save_node to find enclosing FunctionDef
    current = save_node
    while current in parent_map:
        current = parent_map[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Check if this function body contains any setattr() calls
            for child in ast.walk(current):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Name) and child.func.id == 'setattr':
                        return True
            return False
    return False


def _is_simple_objects_chain(objects_node: ast.Attribute, parent_map: dict) -> bool:
    """Check if a Model.objects chain is a trivial lookup.

    Simple: get(pk=...), all(), filter(single_fk=...), filter with up to 3 kwargs
    Complex: exclude(), annotate(), get_or_create(), multi-filter chains with >3 args
    """
    COMPLEX_METHODS = {'exclude', 'annotate', 'aggregate', 'distinct',
                       'get_or_create', 'update_or_create', 'union',
                       'intersection', 'difference', 'values', 'values_list'}
    current = objects_node
    while current in parent_map:
        parent = parent_map[current]
        if isinstance(parent, ast.Call):
            if isinstance(parent.func, ast.Attribute):
                method = parent.func.attr
                if method in COMPLEX_METHODS:
                    return False
                if method == 'filter':
                    if len(parent.args) + len(parent.keywords) > 3:
                        return False
                current = parent
                continue
            else:
                break
        elif isinstance(parent, ast.Attribute):
            current = parent
            continue
        else:
            break
    return True


@rule("RU-002", severity="WARNING", category="python")
def check_views_touching_db():
    """Detect views that call Model.objects or .save()/.delete() directly."""
    violations = []
    db_methods = {
        "save", "create", "update", "delete", "bulk_create",
        "bulk_update", "get_or_create", "update_or_create",
    }
    for py_file in _iter_py_files():
        if not _is_in_views(py_file):
            continue
        # Skip __init__.py (re-exports) and _legacy.py
        if py_file.name in ("__init__.py", "_legacy.py"):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        parent_map = _build_parent_map(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "objects":
                if _is_simple_objects_chain(node, parent_map):
                    continue
                violations.append(
                    Violation(
                        rule_id="RU-002",
                        severity="WARNING",
                        category="python",
                        file=_relpath(py_file),
                        line=node.lineno,
                        message="View directly accessing Model.objects — move query to a service.",
                        snippet=ast.unparse(node) if hasattr(ast, "unparse") else None,
                    )
                )
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr in db_methods:
                    # Skip service method calls: Service.create(), Service.update(), etc.
                    if isinstance(node.func.value, ast.Name):
                        if "service" in node.func.value.id.lower():
                            continue
                    # Skip form.save() and serializer.save() — Django/DRF canonical patterns
                    if node.func.attr == "save":
                        skip = False
                        if isinstance(node.func.value, ast.Call) and isinstance(node.func.value.func, ast.Name):
                            skip = True  # Form(...).save()
                        elif isinstance(node.func.value, ast.Name):
                            name = node.func.value.id.lower()
                            if "serializer" in name or "form" in name:
                                skip = True  # serializer.save(), form.save()
                        # Skip thin FK-field updates: save(update_fields=['single_field'])
                        if not skip and node.keywords:
                            for kw in node.keywords:
                                if kw.arg == 'update_fields' and isinstance(kw.value, ast.List):
                                    if len(kw.value.elts) == 1:
                                        skip = True  # Single-field update, no business logic
                        # Skip generic PATCH: function has setattr() calls = field-set pattern
                        if not skip and _has_setattr_in_enclosing_function(node, tree):
                            skip = True
                        if skip:
                            continue
                    violations.append(
                        Violation(
                            rule_id="RU-002",
                            severity="WARNING",
                            category="python",
                            file=_relpath(py_file),
                            line=node.lineno,
                            message=f"View calling .{node.func.attr}() directly — move to a service.",
                            snippet=ast.unparse(node) if hasattr(ast, "unparse") else None,
                        )
                    )
    return violations


def _is_dict_variable(name_node: ast.expr, parent_map: dict) -> bool:
    """Check if a variable was assigned from a dict literal/comprehension.
    Used to skip dict.update() calls in RU-003 (not a DB write).
    """
    if not isinstance(name_node, ast.Name):
        return False
    # Walk up to find the Assign node for this variable
    current = name_node
    while current in parent_map:
        current = parent_map[current]
        if isinstance(current, ast.Assign):
            if current.targets and isinstance(current.targets[0], ast.Name):
                if current.targets[0].id == name_node.id:
                    val = current.value
                    # Dict literal: {} or {"key": "value"}
                    if isinstance(val, ast.Dict):
                        return True
                    # Dict comprehension: {k: v for k, v in ...}
                    if isinstance(val, ast.DictComp):
                        return True
            break
        # Stop if we hit a function boundary (variable might be a parameter)
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            break
    return False


@rule("RU-003", severity="WARNING", category="python")
def check_missing_atomic():
    """Detect functions with multiple DB writes that lack transaction.atomic."""
    violations = []
    db_write_methods = {"save", "create", "update", "delete", "bulk_create", "bulk_update"}
    for py_file in _iter_py_files():
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        parent_map = _build_parent_map(tree)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if _has_transaction_atomic(node):
                    continue
                write_count = 0
                example_call = None
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Attribute) and child.func.attr in db_write_methods:
                            # Skip form.save() patterns
                            if child.func.attr == "save" and isinstance(child.func.value, ast.Call):
                                continue
                            # Skip dict.update() calls (not QuerySet.update)
                            if child.func.attr == "update" and _is_dict_variable(child.func.value, parent_map):
                                continue
                            write_count += 1
                            if example_call is None:
                                example_call = child
                if write_count >= 2:
                    violations.append(
                        Violation(
                            rule_id="RU-003",
                            severity="WARNING",
                            category="python",
                            file=_relpath(py_file),
                            line=node.lineno,
                            message=f"Function '{node.name}' has {write_count} DB writes but no @transaction.atomic or with transaction.atomic().",
                            snippet=ast.unparse(example_call) if example_call and hasattr(ast, "unparse") else None,
                        )
                    )
    return violations


@rule("RU-004", severity="WARNING", category="python")
def check_bare_delete():
    """Detect .delete() calls on model instances (not QuerySets)."""
    violations = []
    for py_file in _iter_py_files():
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr == "delete":
                    violations.append(
                        Violation(
                            rule_id="RU-004",
                            severity="WARNING",
                            category="python",
                            file=_relpath(py_file),
                            line=node.lineno,
                            message="Bare .delete() call — use is_obsolete = True for immutable audit trail.",
                            snippet=ast.unparse(node) if hasattr(ast, "unparse") else None,
                        )
                    )
    return violations


def _build_parent_map(tree: ast.AST) -> dict:
    """Build a mapping from each AST node to its parent."""
    parent_map = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parent_map[child] = node
    return parent_map


def _is_on_objects(call_node: ast.Call) -> bool:
    """Check if a .all()/.filter() call is on Model.objects (not a related manager)."""
    func = call_node.func
    if not isinstance(func, ast.Attribute):
        return False
    # Walk down: func.value should eventually be Model.objects
    if isinstance(func.value, ast.Attribute) and func.value.attr == "objects":
        return True
    # Also handle: Model.objects.filter(...) where filter is a chain on objects
    return False


def _chain_has_prefetch(call_node: ast.Call, parent_map: dict) -> bool:
    """Walk the call chain in both directions to check for select_related/prefetch_related."""
    # Check parent direction: .all().select_related() wraps .all() in a Call
    # AST: Call(all) -> Attribute(select_related) -> Call(select_related)
    current = call_node
    while current in parent_map:
        parent = parent_map[current]
        if isinstance(parent, ast.Call):
            if isinstance(parent.func, ast.Attribute) and parent.func.attr in ("select_related", "prefetch_related"):
                return True
            break  # Found the wrapping Call, stop walking
        current = parent  # Step through intermediate nodes (Attribute, etc.)

    # Check predecessor direction: .filter(...).select_related()
    current = call_node
    while True:
        func = current.func
        if not isinstance(func, ast.Attribute):
            break
        if func.attr in ("select_related", "prefetch_related"):
            return True
        if isinstance(func.value, ast.Call):
            current = func.value
        else:
            break
    return False


def _chain_has_prefetch_via_reassign(call_node: ast.Call, parent_map: dict, tree: ast.AST) -> bool:
    """Check if a .filter()/.all() chain gets prefetch via variable reassignment.

    Pattern:
        queryset = Model.objects.filter(...)   # no prefetch here
        queryset = queryset.select_related(...) # but added later on same variable
    """
    # Find the Assign that wraps this call
    current = call_node
    assign_node = None
    var_name = None
    while current in parent_map:
        current = parent_map[current]
        if isinstance(current, ast.Assign):
            if current.targets and isinstance(current.targets[0], ast.Name):
                assign_node = current
                var_name = current.targets[0].id
                break
        # Stop if we hit another Call (nested expression, not an assignment)
        if isinstance(current, ast.Call) and current != call_node:
            break

    if not var_name:
        return False

    # Find enclosing function
    current = assign_node
    func_node = None
    while current in parent_map:
        current = parent_map[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_node = current
            break

    if not func_node:
        return False

    # Walk function body for select_related/prefetch_related on same variable
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in ('select_related', 'prefetch_related'):
                if isinstance(node.func.value, ast.Name) and node.func.value.id == var_name:
                    return True

    return False


def _chain_ends_with_terminal(call_node: ast.Call, parent_map: dict) -> bool:
    """Walk down the call chain to check if it ends with values/exists/count/etc."""
    TERMINAL = {"values", "values_list", "exists", "count", "aggregate", "first", "get", "earliest", "latest"}
    current = call_node
    while current in parent_map:
        parent = parent_map[current]
        if isinstance(parent, ast.Call) and isinstance(parent.func, ast.Attribute):
            if parent.func.attr in TERMINAL:
                return True
            current = parent
            continue
        current = parent
    return False


def _filter_is_scalar_only(filter_node: ast.Call) -> bool:
    """Check if a .filter() call only uses scalar field lookups (no __ joins).
    e.g., .filter(is_obsolete=False, status__isnull=True) — scalar fields only.
    e.g., .filter(task__status__personality='DOING') — has a join, needs prefetch.
    """
    for kw in filter_node.keywords:
        if kw.arg and '__' in kw.arg:
            # Check if the __ part refers to a related field (join)
            # Simple operators: __isnull, __gt, __lt, __gte, __lte, __exact, __in, __icontains, __contains, __startswith
            parts = kw.arg.split('__', 1)
            if len(parts) == 2:
                operator = parts[1].lower()
                if operator not in ('isnull', 'gt', 'lt', 'gte', 'lte', 'exact',
                                    'in', 'icontains', 'contains', 'startswith',
                                    'range', 'regex', 'iregex', 'year', 'month',
                                    'day', 'week_day', 'hour', 'minute', 'second'):
                    return False  # Cross-model join, needs prefetch
    return True  # All filters are on scalar fields


def _chain_has_values_list(call_node: ast.Call, parent_map: dict) -> bool:
    """Check if the chain ends with .values_list() — never hydrates model instances."""
    TERMINAL = {"values", "values_list"}
    current = call_node
    visited = set()
    while current in parent_map and id(current) not in visited:
        visited.add(id(current))
        parent = parent_map[current]
        if isinstance(parent, ast.Call) and isinstance(parent.func, ast.Attribute):
            if parent.func.attr in TERMINAL:
                return True
            current = parent
            continue
        current = parent
    return False


@rule("RU-005", severity="WARNING", category="python")
def check_missing_prefetch():
    """Detect QuerySets missing select_related or prefetch_related in views."""
    violations = []
    for py_file in _iter_py_files():
        if not _is_in_views(py_file):
            continue
        if py_file.name == "__init__.py":
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        parent_map = _build_parent_map(tree)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr not in ("all", "filter"):
                    continue

                # .all() on a model table is typically a lookup table with no FK
                # fields worth prefetching. N+1 risk is negligible.
                if node.func.attr == "all":
                    continue

                # Skip related manager queries (e.g., instance.items.filter(...))
                if not _is_on_objects(node):
                    continue

                # Skip if chain already has select_related/prefetch_related
                if _chain_has_prefetch(node, parent_map):
                    continue

                # Skip if chain ends with a terminal operation (values, exists, count, etc.)
                if _chain_ends_with_terminal(node, parent_map):
                    continue

                # Skip if filter only uses scalar fields (no __ joins to related models)
                if node.func.attr == "filter" and _filter_is_scalar_only(node):
                    continue

                # Skip if prefetch is added via variable reassignment later in function
                if _chain_has_prefetch_via_reassign(node, parent_map, tree):
                    continue

                violations.append(
                    Violation(
                        rule_id="RU-005",
                        severity="WARNING",
                        category="python",
                        file=_relpath(py_file),
                        line=node.lineno,
                        message=f"QuerySet .{node.func.attr}() missing .select_related() or .prefetch_related().",
                        snippet=ast.unparse(node) if hasattr(ast, "unparse") else None,
                    )
                )
    return violations


@rule("RU-006", severity="WARNING", category="python")
def check_missing_type_hints():
    """Flag service functions missing return type annotations."""
    violations = []
    for py_file in _iter_py_files():
        if not _is_in_services(py_file):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_"):
                    continue
                if node.returns is None:
                    violations.append(
                        Violation(
                            rule_id="RU-006",
                            severity="WARNING",
                            category="python",
                            file=_relpath(py_file),
                            line=node.lineno,
                            message=f"Service function '{node.name}' missing return type annotation.",
                            snippet=f"def {node.name}(...):",
                        )
                    )
    return violations


@rule("RU-008", severity="WARNING", category="python")
def check_cross_domain_imports():
    """Flag service files importing from other domain services."""
    violations = []
    for py_file in _iter_py_files():
        if not _is_in_services(py_file):
            continue
        domain = _classify_file_domain(py_file)
        if not domain:
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module = getattr(node, "module", None) or ""
                if not module and isinstance(node, ast.Import) and node.names:
                    module = node.names[0].name
                if "services" in module:
                    imported_domain = module.split(".")[-1]
                    if imported_domain.startswith("_"):
                        continue
                    if imported_domain != domain and imported_domain != "__init__":
                        imported_domain_clean = imported_domain.replace("_service", "")
                        domain_clean = domain.replace("_service", "")
                        if imported_domain_clean != domain_clean:
                            violations.append(
                                Violation(
                                    rule_id="RU-008",
                                    severity="WARNING",
                                    category="python",
                                    file=_relpath(py_file),
                                    line=node.lineno,
                                    message=f"Cross-domain import: '{domain}' imports from '{imported_domain_clean}'. Verify this coupling is intentional.",
                                    snippet=f"from {module} import ...",
                                )
                            )
    return violations


@rule("RU-010", severity="WARNING", category="python")
def check_print_data_leaks():
    """Flag print() or logging.debug() in production code."""
    violations = []
    for py_file in _iter_py_files():
        if "management" in py_file.parts or "commands" in py_file.parts:
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "print":
                    violations.append(
                        Violation(
                            rule_id="RU-010",
                            severity="WARNING",
                            category="python",
                            file=_relpath(py_file),
                            line=node.lineno,
                            message="print() call in non-test/non-management code — potential data leak.",
                            snippet=ast.unparse(node) if hasattr(ast, "unparse") else "print(...)",
                        )
                    )
    return violations


@rule("RU-011", severity="ERROR", category="python")
def check_eager_getattr_default():
    """
    Detect getattr() with an eager default that calls a property/method.

    Python evaluates the default argument before getattr() runs, so
    `getattr(obj, '_cache', obj.expensive_property)` always calls
    `expensive_property`. This is a common source of N+1 queries when the
    property hits the database.
    """
    violations = []
    for py_file in _iter_py_files():
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Name) or node.func.id != "getattr":
                continue
            if len(node.args) < 3:
                continue
            default_arg = node.args[2]
            # Flag defaults that are attribute/method calls or subscripts on attributes.
            if isinstance(default_arg, (ast.Attribute, ast.Subscript, ast.Call)):
                # Skip simple constants or names — those are safe.
                if isinstance(default_arg, ast.Call):
                    # getattr(obj, 'x', some_func()) is also eager; flag it.
                    pass
                violations.append(
                    Violation(
                        rule_id="RU-011",
                        severity="ERROR",
                        category="python",
                        file=_relpath(py_file),
                        line=node.lineno,
                        message="getattr() default argument is eager: it is evaluated even when the attribute exists. Use `hasattr` + explicit fallback to avoid N+1 side effects.",
                        snippet=ast.unparse(node) if hasattr(ast, "unparse") else None,
                    )
                )
    return violations


# ──────────────────────────────────────────────
# RU-013: .save() in a loop — use bulk_create/bulk_update
# ──────────────────────────────────────────────

# Methods whose call on an object inside a loop is a red flag for RU-013
_BULK_CANDIDATE_METHODS = {"save", "create", "update"}
# Allow: .save() inside a transaction.atomic() block (wrap is intentional)


@rule("RU-013", severity="ERROR", category="python")
def check_save_in_loop():
    """
    Detect .save()/.create()/.update() calls inside for/while loops.

    On the Raspberry Pi, N individual INSERT/UPDATE statements issued inside
    a loop can lock the DB for seconds. Use bulk_create() or bulk_update()
    instead. A loop with a single .save() inside a transaction.atomic() block
    is exempt (the atomic wrap is intentional).
    """
    violations = []
    for py_file in _iter_py_files():
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        parent_map = _build_parent_map(tree)

        for node in ast.walk(tree):
            # Only look at save/create/update method calls
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in _BULK_CANDIDATE_METHODS:
                continue

            # Walk up to find enclosing loop
            current = node
            loop_node = None
            while current in parent_map:
                current = parent_map[current]
                if isinstance(current, (ast.For, ast.While, ast.AsyncFor)):
                    loop_node = current
                    break
                # Stop if we hit a function/class boundary before finding a loop
                if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    break

            if loop_node is None:
                continue

            # Exempt: if the loop body is wrapped in transaction.atomic()
            if _is_inside_atomic_context(node, parent_map, loop_node):
                continue

            # Exempt: form.save() and serializer.save() (canonical Django patterns)
            if node.func.attr == "save":
                if isinstance(node.func.value, ast.Attribute) and node.func.value.attr == "save":
                    continue
                if isinstance(node.func.value, ast.Call) and isinstance(node.func.value.func, ast.Name):
                    continue  # Form(...).save()
                if isinstance(node.func.value, ast.Name):
                    name = node.func.value.id.lower()
                    if "serializer" in name or "form" in name:
                        continue  # serializer.save(), form.save()

            # Exempt: .update() is always a single SQL UPDATE on a QuerySet — bulk by definition
            # (Model.objects.filter(...).update(...), qs.update(...), variable.update(...))
            if node.func.attr == "update":
                continue

            # Exempt: *Service.create() / *Service.update() — service orchestration,
            # not a direct model write
            if node.func.attr in ("create", "update"):
                if isinstance(node.func.value, ast.Name):
                    name_lower = node.func.value.id.lower()
                    if "service" in name_lower:
                        continue  # InvoiceService.create(...), etc.
                elif isinstance(node.func.value, ast.Attribute):
                    attr_lower = node.func.value.attr.lower()
                    if "service" in attr_lower:
                        continue  # self.invoice_service.create(...), etc.

            violated_method = node.func.attr
            violations.append(
                Violation(
                    rule_id="RU-013",
                    severity="ERROR",
                    category="python",
                    file=_relpath(py_file),
                    line=node.lineno,
                    message=(
                        f".{violated_method}() inside a for/while loop — "
                        f"use bulk_{'create' if violated_method == 'create' else 'update'}() "
                        f"or collect instances and .save() outside the loop. "
                        f"On a Pi, N individual writes can lock the DB for seconds."
                    ),
                    snippet=ast.unparse(node) if hasattr(ast, "unparse") else None,
                )
            )

    return violations


def _is_inside_atomic_context(save_node: ast.Call, parent_map: dict, loop_node: ast.AST) -> bool:
    """Check if save_node is inside a `with transaction.atomic():` block."""
    current = save_node
    while current in parent_map:
        current = parent_map[current]
        if current is loop_node:
            return False  # Reached the loop node without finding atomic
        if isinstance(current, ast.With):
            for item in current.items:
                if isinstance(item.context_expr, ast.Call):
                    ce = item.context_expr
                    if isinstance(ce.func, ast.Attribute):
                        if (
                            isinstance(ce.func.value, ast.Name)
                            and ce.func.value.id == "transaction"
                            and ce.func.attr == "atomic"
                        ):
                            return True
        # Don't cross function boundaries during search
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if current is not loop_node:
                return False
    return False


# ──────────────────────────────────────────────
# RU-014: Expensive log message formatting in loops
# ──────────────────────────────────────────────

_LOG_METHODS = {"debug", "info", "warning", "warn", "error", "critical", "exception"}


@rule("RU-014", severity="WARNING", category="python")
def check_logger_in_loop():
    """
    Detect logger calls with f-strings or .format() inside loop bodies.

    Python evaluates f-string/format arguments eagerly, even when the log
    level is disabled. Inside a loop, this creates N wasted string allocations.

    Fix: precompute `enabled = logger.isEnabledFor(logging.DEBUG)` outside
    the loop, then guard the log call with `if enabled:`.
    """
    violations = []
    for py_file in _iter_py_files():
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        parent_map = _build_parent_map(tree)

        for node in ast.walk(tree):
            # Find log method calls: logger.debug(...), logger.info(...), etc.
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in _LOG_METHODS:
                continue

            # Only flag if called on a variable named 'logger' (or ending in _logger)
            if not isinstance(node.func.value, ast.Name):
                continue
            if not (
                node.func.value.id == "logger"
                or node.func.value.id.endswith("_logger")
            ):
                continue

            # Check for f-string args — these evaluate eagerly
            has_format_str = False
            for arg in node.args:
                if isinstance(arg, ast.JoinedStr):  # f"..."
                    has_format_str = True
                    break
                if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute):
                    if arg.func.attr == "format":  # "...".format(...)
                        has_format_str = True
                        break

            if not has_format_str:
                continue

            # Walk up to find enclosing loop
            current = node
            while current in parent_map:
                current = parent_map[current]
                if isinstance(current, (ast.For, ast.While, ast.AsyncFor)):
                    violations.append(
                        Violation(
                            rule_id="RU-014",
                            severity="WARNING",
                            category="python",
                            file=_relpath(py_file),
                            line=node.lineno,
                            message=(
                                f"logger.{node.func.attr}() with f-string/format "
                                f"inside a loop — string formatting executes eagerly "
                                f"even when the log level is disabled. Precompute "
                                f"`isEnabledFor` outside the loop and guard the call."
                            ),
                            snippet=ast.unparse(node) if hasattr(ast, "unparse") else None,
                        )
                    )
                    break
                if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    break

    return violations


# ──────────────────────────────────────────────
# RU-012: Model property accessed relations vs view prefetch
# ──────────────────────────────────────────────

def _is_related_manager_call(node: ast.Call) -> str | None:
    """
    Detect calls like self.task_allocations.filter(...) in model properties.
    Returns the relation name (e.g. 'task_allocations') or None.
    """
    if not isinstance(node.func, ast.Attribute):
        return None
    if node.func.attr not in ('filter', 'all', 'exists', 'count', 'get',
                               'annotate', 'aggregate', 'exclude', 'order_by',
                               'select_related', 'prefetch_related'):
        return None
    # Check if the value is self.<relation>
    if not isinstance(node.func.value, ast.Attribute):
        return None
    if not (isinstance(node.func.value.value, ast.Name)
            and node.func.value.value.id == 'self'):
        return None
    # Skip _id suffixed attributes (local FK fields, not related managers)
    if node.func.value.attr.endswith('_id'):
        return None
    # Skip Django model internals
    if node.func.value.attr.startswith('_'):
        return None
    return node.func.value.attr


def _build_model_property_relations() -> dict[str, set[str]]:
    """
    Scan model files for @property methods that access related managers.

    Returns:
        dict mapping model class name → set of relation names accessed
        by properties (e.g. {'InventoryItem': {'task_allocations'}})
    """
    model_relations: dict[str, set[str]] = {}
    models_dir = _get_src_root() / "core" / "models"
    if not models_dir.is_dir():
        return model_relations

    for py_file in models_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            # Only consider Django model classes (inherit from models.Model or TimeStampedModel)
            bases = [
                b.id if isinstance(b, ast.Name) else (
                    b.attr if isinstance(b, ast.Attribute) else ''
                )
                for b in node.bases
            ]
            is_model = any(
                b in ('Model', 'TimeStampedModel', 'PolymorphicModel')
                for b in bases
            )
            if not is_model:
                continue

            model_name = node.name
            relations: set[str] = set()

            for item in node.body:
                if not isinstance(item, ast.FunctionDef):
                    continue
                # Check for @property decorator
                is_property = any(
                    isinstance(d, ast.Name) and d.id == 'property'
                    for d in item.decorator_list
                )
                if not is_property:
                    continue

                # Walk the property body for related manager calls
                for child in ast.walk(item):
                    if isinstance(child, ast.Call):
                        rel = _is_related_manager_call(child)
                        if rel:
                            relations.add(rel)

            if relations:
                model_relations[model_name] = relations

    return model_relations


def _extract_prefetch_relations(node: ast.Call, parent_map: dict) -> set[str]:
    """
    Walk UP from a .filter()/.all() call through parent_map to find any
    enclosing .select_related() or .prefetch_related() calls and extract
    their relation arguments.

    Handles both string args and nested Prefetch('relation', ...) calls.
    """
    relations: set[str] = set()

    def _add_from_args(args):
        for arg in args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                parts = arg.value.split('__')
                relations.add(parts[0])
            elif isinstance(arg, ast.Call) and arg.args:
                if isinstance(arg.args[0], ast.Constant) and isinstance(arg.args[0].value, str):
                    parts = arg.args[0].value.split('__')
                    relations.add(parts[0])

    # Walk up through parent_map looking for select_related / prefetch_related
    current = node
    while current in parent_map:
        parent = parent_map[current]
        if isinstance(parent, ast.Call) and isinstance(parent.func, ast.Attribute):
            if parent.func.attr in ('select_related', 'prefetch_related'):
                _add_from_args(parent.args)
            # Continue walking up through chain methods
            if parent.func.attr in ('filter', 'all', 'exclude', 'annotate',
                                     'order_by', 'distinct', 'select_related',
                                     'prefetch_related', 'values', 'values_list'):
                current = parent
                continue
        elif isinstance(parent, ast.Attribute):
            current = parent
            continue
        current = parent

    return relations


def _extract_prefetch_relations_via_reassign(
    call_node: ast.Call, var_name: str, parent_map: dict, tree: ast.AST
) -> set[str]:
    """
    Check for prefetch relations added via variable reassignment:
        qs = Model.objects.filter(...)
        qs = qs.select_related('foo')
    """
    relations: set[str] = set()

    # Find enclosing function
    current = call_node
    func_node = None
    while current in parent_map:
        current = parent_map[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_node = current
            break

    if not func_node:
        return relations

    for node in ast.walk(func_node):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in ('select_related', 'prefetch_related'):
                if isinstance(node.func.value, ast.Name) and node.func.value.id == var_name:
                    for arg in node.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            parts = arg.value.split('__')
                            relations.add(parts[0])
                        elif isinstance(arg, ast.Call) and arg.args:
                            if isinstance(arg.args[0], ast.Constant):
                                parts = arg.args[0].value.split('__')
                                relations.add(parts[0])

    return relations


def _resolve_model_name(queryset_node: ast.Call) -> str | None:
    """
    Try to resolve Model.objects.filter(...) → 'ModelName'.

    Handles patterns like:
        InventoryItem.objects.filter(...)
        from core.models import InventoryItem; InventoryItem.objects.filter(...)
    """
    if not isinstance(queryset_node.func, ast.Attribute):
        return None
    # queryset_node.func = Attribute(value=..., attr='filter')
    # queryset_node.func.value should be Attribute(value=Model, attr='objects')
    base = queryset_node.func.value
    if not isinstance(base, ast.Attribute) or base.attr != 'objects':
        return None
    if isinstance(base.value, ast.Name):
        return base.value.id
    return None


@rule("RU-012", severity="WARNING", category="python")
def check_property_accessed_relations():
    """
    Detect N+1 query risk: model @property accesses relations not in
    .select_related()/.prefetch_related() of view querysets.

    Example: InventoryItem.status property calls self.task_allocations.filter(),
    but the view queryset lacks prefetch_related('task_allocations').
    """
    violations = []

    # Pass 1: Build model → property-accessed-relations map
    model_property_relations = _build_model_property_relations()
    if not model_property_relations:
        return violations

    # Pass 2: Check view querysets
    for py_file in _iter_py_files():
        if not _is_in_views(py_file):
            continue
        if py_file.name in ("__init__.py", "_legacy.py"):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        parent_map = _build_parent_map(tree)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in ('filter', 'all'):
                continue

            # Resolve which model this queryset is on
            model_name = _resolve_model_name(node)
            if not model_name or model_name not in model_property_relations:
                continue

            # Get relations that model properties access
            needed_relations = model_property_relations[model_name]
            if not needed_relations:
                continue

            # Skip values_list/values queries — they never hydrate model instances
            if _chain_has_values_list(node, parent_map):
                continue

            # Get relations already in select_related/prefetch_related
            prefetched = _extract_prefetch_relations(node, parent_map)

            # Also check via reassignment
            var_name = None
            current = node
            while current in parent_map:
                current = parent_map[current]
                if isinstance(current, ast.Assign):
                    if current.targets and isinstance(current.targets[0], ast.Name):
                        var_name = current.targets[0].id
                        break
                if isinstance(current, ast.Call):
                    break

            if var_name:
                prefetched |= _extract_prefetch_relations_via_reassign(
                    node, var_name, parent_map, tree
                )

            # Find missing relations
            missing = needed_relations - prefetched
            if missing:
                for rel in sorted(missing):
                    violations.append(
                        Violation(
                            rule_id="RU-012",
                            severity="WARNING",
                            category="python",
                            file=_relpath(py_file),
                            line=node.lineno,
                            message=(
                                f"Model '{model_name}' @property accesses '{rel}' "
                                f"but queryset lacks .select_related()/.prefetch_related() "
                                f"— potential N+1 query per item."
                            ),
                            snippet=ast.unparse(node)
                            if hasattr(ast, "unparse")
                            else f"{model_name}.objects...",
                        )
                    )

    return violations
