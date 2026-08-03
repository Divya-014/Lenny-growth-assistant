import os
from sentence_transformers import SentenceTransformer

try:
    print("Attempting to load sentence-transformers/all-MiniLM-L6-v2...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    print("Success loading model!")
    print(f"Model: {model}")
except Exception as e:
    import traceback
    print("Failed to load model:")
    traceback.print_exc()
