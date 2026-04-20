def try_imports():
    checks = [
        ('create_retrieval_chain', [
            "langchain.chains",
            "langchain_community.chains",
            "langchain_classic.chains",
        ]),
        ('create_stuff_documents_chain', [
            "langchain.chains.combine_documents",
            "langchain_community.chains.combine_documents",
            "langchain_classic.chains.combine_documents",
        ])
    ]
    for func, locations in checks:
        found = False
        for loc in locations:
            try:
                mod = __import__(loc, fromlist=[func])
                if hasattr(mod, func):
                    print(f"SUCCESS: {func} found in {loc}")
                    found = True
                    break
            except ImportError:
                pass
        if not found:
            print(f"FAILED: {func} not found anywhere")

if __name__ == "__main__":
    try_imports()
