import os
import pkg_resources

def find_function_in_packages(func_name):
    for dist in pkg_resources.working_set:
        print(f"Checking {dist.project_name} ({dist.version})...")
        # This might be slow, so let's just check the ones that look like langchain
        if "langchain" in dist.project_name.lower():
            # Try to walk the package
            package_path = dist.location
            # This is too complex. Let's just try to import common locations
            pass

def try_imports():
    locations = [
        "langchain.chains",
        "langchain_community.chains",
        "langchain_classic.chains",
        "langchain.chains.retrieval",
        "langchain_core.chains"
    ]
    for loc in locations:
        try:
            mod = __import__(loc, fromlist=['create_retrieval_chain'])
            if hasattr(mod, 'create_retrieval_chain'):
                print(f"SUCCESS: create_retrieval_chain found in {loc}")
            else:
                print(f"PARTIAL: {loc} exists but no create_retrieval_chain")
        except ImportError as e:
            print(f"FAILED: {loc} ({e})")

if __name__ == "__main__":
    try_imports()
