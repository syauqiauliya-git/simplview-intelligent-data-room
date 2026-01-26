import pandasai.llm
import pkgutil

print("--- Inspecting pandasai.llm ---")
print("Available classes in top-level:", dir(pandasai.llm))

print("\n--- Submodules ---")
path = pandasai.llm.__path__
for importer, modname, ispkg in pkgutil.iter_modules(path):
    print(f"Found submodule: {modname}")