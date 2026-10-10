from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"


def load_knowledge():
    """Load text files and extract text from PDFs in knowledge/."""
    documents = []

    if not KNOWLEDGE_DIR.exists():
        raise FileNotFoundError("The knowledge folder does not exist.")

    for path in KNOWLEDGE_DIR.iterdir():
        if path.suffix.lower() == ".txt":
            text = path.read_text(encoding="utf-8").strip()

            if text:
                documents.append({
                    "source": path.name,
                    "text": text
                })

        elif path.suffix.lower() == ".pdf":
            import pymupdf

            with pymupdf.open(path) as pdf:
                text = "\n".join(page.get_text() for page in pdf)

            if text.strip():
                documents.append({
                    "source": path.name,
                    "text": text.strip()
                })

    return documents


def split_into_chunks(text, chunk_size=120, overlap=25):
    """Split text into overlapping word chunks."""
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))

        if end == len(words):
            break

        start = end - overlap

    return chunks


def build_index():
    """Build a TF-IDF search index from the knowledge files."""
    documents = load_knowledge()
    chunks = []

    for document in documents:
        for chunk in split_into_chunks(document["text"]):
            chunks.append({
                "source": document["source"],
                "text": chunk
            })

    if not chunks:
        raise ValueError(
            "No knowledge documents found. Add a text file "
            "to the knowledge folder."
        )

    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        stop_words="english"
    )

    matrix = vectorizer.fit_transform(
        [chunk["text"] for chunk in chunks]
    )

    return vectorizer, matrix, chunks


def retrieve(query, vectorizer, matrix, chunks, top_k=3):
    """Retrieve the most relevant knowledge chunks."""
    query_vector = vectorizer.transform([query])
    scores = cosine_similarity(query_vector, matrix).ravel()
    ranked_indices = scores.argsort()[::-1][:top_k]

    results = []

    for index in ranked_indices:
        score = float(scores[index])

        if score > 0:
            results.append({
                "source": chunks[index]["source"],
                "text": chunks[index]["text"],
                "score": round(score, 3)
            })

    return results