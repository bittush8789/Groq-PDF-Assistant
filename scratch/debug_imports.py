try:
    from langchain.chains import create_retrieval_chain
    print("langchain.chains works")
except ImportError as e:
    print(f"langchain.chains failed: {e}")

try:
    from langchain.chains.retrieval import create_retrieval_chain
    print("langchain.chains.retrieval works")
except ImportError as e:
    print(f"langchain.chains.retrieval failed: {e}")

try:
    import langchain
    print(f"langchain version: {langchain.__version__}")
    print(f"langchain path: {langchain.__file__}")
except ImportError as e:
    print(f"langchain failed: {e}")
