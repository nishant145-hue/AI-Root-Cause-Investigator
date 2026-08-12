import ast
import importlib.metadata
from pathlib import Path

ROOT = Path("app")

stdlib = {
    "abc", "asyncio", "base64", "collections", "contextlib",
    "csv", "datetime", "decimal", "enum", "functools", "hashlib",
    "hmac", "html", "http", "inspect", "io", "itertools", "json",
    "logging", "math", "mimetypes", "os", "pathlib", "re", "secrets",
    "shutil", "socket", "sqlite3", "statistics", "string", "subprocess",
    "sys", "tempfile", "textwrap", "time", "traceback", "typing",
    "uuid", "warnings", "xml", "zipfile"
}

imports = set()

for file in ROOT.rglob("*.py"):
    try:
        tree = ast.parse(file.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Could not parse {file}: {exc}")
        continue

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])

        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                imports.add(node.module.split(".")[0])

imports -= stdlib
imports = sorted(imports)

package_map = importlib.metadata.packages_distributions()

print("\n=== THIRD-PARTY IMPORTS USED BY APP ===\n")

for name in imports:
    distributions = package_map.get(name, [])
    if distributions:
        print(f"{name:<25} -> {', '.join(distributions)}")
    else:
        print(f"{name:<25} -> [NOT FOUND IN INSTALLED DISTRIBUTIONS]")

print("\n=== DONE ===")
