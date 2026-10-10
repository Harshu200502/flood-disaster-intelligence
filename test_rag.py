
from rag import build_index, retrieve

vectorizer, matrix, chunks = build_index()

queries = [
    "What should people avoid during flooding?",
    "What should people do during evacuation?",
    "Satellite-derived flood extent, rainfall measurements, "
    "population exposure estimates, and data limitations"
]

for query in queries:
    print(f"\nQUERY: {query}")
    results = retrieve(query, vectorizer, matrix, chunks, top_k=2)

    if not results:
        print("No relevant passages found.")
        continue

    for item in results:
        print(f"Source: {item['source']}")
        print(f"Score: {item['score']}")
        print(f"Passage: {item['text']}\n")
