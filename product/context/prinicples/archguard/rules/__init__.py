from collections.abc import Callable

_registry: list[Callable] = []


def rule(rule_id: str, severity: str = "ERROR", category: str = "python"):
    """Decorator to register an architecture guard rule."""

    def decorator(fn: Callable):
        fn.rule_id = rule_id
        fn.severity = severity
        fn.category = category
        _registry.append(fn)
        return fn

    return decorator


def discover() -> list[Callable]:
    """Return all registered rules in registration order."""
    return list(_registry)
