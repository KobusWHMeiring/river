"""Self-tests for architecture guard rules."""
import os
import tempfile
from pathlib import Path

# Import the rule functions directly
from scripts.archguard.rules.python_ast import (
    check_silenced_exceptions,
    check_views_touching_db,
    check_missing_atomic,
    check_bare_delete,
    check_missing_prefetch,
    check_missing_type_hints,
    check_cross_domain_imports,
    check_print_data_leaks,
)
from scripts.archguard.rules.templates import (
    check_cdn_in_templates,
    check_template_nesting,
)


class TestTempProject:
    """Create a temporary project structure for testing rules."""

    def setup_method(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.tmpdir.name)
        # Create minimal src structure
        Path("src").mkdir()
        Path("src/templates").mkdir(parents=True)

    def teardown_method(self):
        os.chdir(self.old_cwd)
        self.tmpdir.cleanup()

    def _write_file(self, relpath: str, content: str):
        path = Path(relpath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _write_view(self, name: str, content: str):
        Path("src/core/views").mkdir(parents=True, exist_ok=True)
        self._write_file(f"src/core/views/{name}", content)

    def _write_service(self, name: str, content: str):
        Path("src/core/services").mkdir(parents=True, exist_ok=True)
        self._write_file(f"src/core/services/{name}", content)


class TestPythonAST(TestTempProject):
    """Test Python AST rules."""

    def test_silenced_except_detected(self):
        self._write_file(
            "src/some_file.py",
            "def bad():\n"
            "    try:\n"
            "        risky()\n"
            "    except Exception:\n"
            "        pass\n",
        )
        violations = check_silenced_exceptions()
        assert len(violations) == 1
        assert violations[0].rule_id == "RU-001"

    def test_proper_except_not_flagged(self):
        self._write_file(
            "src/some_file.py",
            "def good():\n"
            "    try:\n"
            "        risky()\n"
            "    except Exception as e:\n"
            "        logger.error('Failed', exc_info=e)\n"
            "        raise\n",
        )
        violations = check_silenced_exceptions()
        assert len(violations) == 0

    def test_view_touching_db_detected(self):
        self._write_view(
            "test_view.py",
            "def my_view(request):\n"
            "    items = Invoice.objects.filter(status='PAID')\n"
            "    return items\n",
        )
        violations = check_views_touching_db()
        assert len(violations) >= 1
        assert any(v.rule_id == "RU-002" for v in violations)

    def test_non_view_touching_db_not_flagged(self):
        self._write_service(
            "test_service.py",
            "def get_items():\n" "    return Invoice.objects.filter(status='PAID')\n",
        )
        violations = check_views_touching_db()
        assert len(violations) == 0

    def test_missing_atomic_detected(self):
        self._write_service(
            "test_service.py",
            "def create_things():\n"
            "    a = Thing()\n"
            "    a.save()\n"
            "    b = Thing()\n"
            "    b.save()\n",
        )
        violations = check_missing_atomic()
        assert len(violations) >= 1
        assert any(v.rule_id == "RU-003" for v in violations)

    def test_atomic_present_not_flagged(self):
        self._write_service(
            "test_service.py",
            "from django.db import transaction\n\n"
            "@transaction.atomic\n"
            "def create_things():\n"
            "    a = Thing()\n"
            "    a.save()\n"
            "    b = Thing()\n"
            "    b.save()\n",
        )
        violations = check_missing_atomic()
        assert all(v.rule_id != "RU-003" for v in violations)

    def test_bare_delete_detected(self):
        self._write_file(
            "src/some_file.py",
            "def bad(instance):\n" "    instance.delete()\n",
        )
        violations = check_bare_delete()
        assert len(violations) >= 1
        assert any(v.rule_id == "RU-004" for v in violations)

    def test_view_missing_prefetch_detected(self):
        self._write_view(
            "test_view.py",
            "def bad():\n" "    return Model.objects.all()\n",
        )
        violations = check_missing_prefetch()
        assert len(violations) >= 1
        assert any(v.rule_id == "RU-005" for v in violations)

    def test_view_with_prefetch_not_flagged(self):
        self._write_view(
            "test_view.py",
            "def good():\n"
            "    return Model.objects.all().select_related('fk')\n",
        )
        violations = check_missing_prefetch()
        assert all(v.rule_id != "RU-005" for v in violations)

    def test_missing_type_hints_detected(self):
        self._write_service(
            "test_service.py",
            "def get_stuff():\n" "    return 42\n",
        )
        violations = check_missing_type_hints()
        assert len(violations) >= 1
        assert any(v.rule_id == "RU-006" for v in violations)

    def test_type_hints_present_not_flagged(self):
        self._write_service(
            "test_service.py",
            "def get_stuff() -> int:\n" "    return 42\n",
        )
        violations = check_missing_type_hints()
        assert all(v.rule_id != "RU-006" for v in violations)

    def test_cross_domain_import_detected(self):
        self._write_service(
            "finance_service.py",
            "from core.services.inventory_service import check_stock\n",
        )
        violations = check_cross_domain_imports()
        assert len(violations) >= 1
        assert any(v.rule_id == "RU-008" for v in violations)

    def test_print_data_leak_detected(self):
        self._write_file(
            "src/some_file.py",
            "def bad(password):\n" "    print(password)\n",
        )
        violations = check_print_data_leaks()
        assert len(violations) >= 1
        assert any(v.rule_id == "RU-010" for v in violations)


class TestTemplates(TestTempProject):
    """Test template rules."""

    def test_cdn_in_template_detected(self):
        self._write_file(
            "src/templates/test.html",
            '<script src="https://cdn.example.com/lib.js"></script>',
        )
        violations = check_cdn_in_templates()
        assert len(violations) >= 1
        assert any(v.rule_id == "RU-007" for v in violations)

    def test_no_cdn_not_flagged(self):
        self._write_file(
            "src/templates/test.html",
            '<script src="/static/js/lib.js"></script>',
        )
        violations = check_cdn_in_templates()
        assert len(violations) == 0

    def test_deep_nesting_detected(self):
        self._write_file(
            "src/templates/test.html",
            "{% if a %}\n"
            "  {% if b %}\n"
            "    {% if c %}\n"
            "      {% if d %}\n"
            "        deep\n"
            "      {% endif %}\n"
            "    {% endif %}\n"
            "  {% endif %}\n"
            "{% endif %}\n",
        )
        violations = check_template_nesting()
        assert len(violations) >= 1
        assert any(v.rule_id == "RU-009" for v in violations)

    def test_shallow_nesting_not_flagged(self):
        self._write_file(
            "src/templates/test.html",
            "{% if a %}\n"
            "  {% if b %}\n"
            "    ok\n"
            "  {% endif %}\n"
            "{% endif %}\n",
        )
        violations = check_template_nesting()
        assert len(violations) == 0


class TestSkippedDirectories(TestTempProject):
    """Test that skipped directories are not scanned."""

    def test_migrations_skipped(self):
        Path("src/core/migrations").mkdir(parents=True)
        self._write_file(
            "src/core/migrations/0001_test.py",
            "def bad():\n"
            "    try:\n"
            "        x = 1\n"
            "    except:\n"
            "        pass\n",
        )
        violations = check_silenced_exceptions()
        assert len(violations) == 0

    def test_tests_skipped(self):
        Path("src/core/tests").mkdir(parents=True)
        self._write_file(
            "src/core/tests/test_bad.py",
            "def bad():\n"
            "    try:\n"
            "        x = 1\n"
            "    except:\n"
            "        pass\n",
        )
        violations = check_silenced_exceptions()
        assert len(violations) == 0

    def test_management_commands_skipped(self):
        Path("src/core/management/commands").mkdir(parents=True)
        self._write_file(
            "src/core/management/commands/bad.py",
            "def bad():\n"
            "    try:\n"
            "        x = 1\n"
            "    except:\n"
            "        pass\n",
        )
        violations = check_silenced_exceptions()
        assert len(violations) == 0
