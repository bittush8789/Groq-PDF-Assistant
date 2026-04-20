try:
    from langchain_classic.chains import create_retrieval_chain
    print("create_retrieval_chain success")
except ImportError:
    print("create_retrieval_chain fail")

try:
    from langchain_classic.chains.combine_documents import create_stuff_documents_chain
    print("create_stuff_documents_chain success")
except ImportError:
    print("create_stuff_documents_chain fail")
