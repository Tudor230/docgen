import importlib

def load_backend(name: str):
    try:
        return importlib.import_module(f"docgen.backends.{name}.parser")
    except ModuleNotFoundError as e:
        raise ImportError(f"Backend '{name}' not found.") from e