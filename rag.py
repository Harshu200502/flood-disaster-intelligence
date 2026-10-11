
from pathlib import Path
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"

# Cache the index so repeated queries do not rebuild it.
_INDEX_CACHE = None
_INDEX_CACHE_SIGNATURE = None


def load_knowledge():
    """Load text files and extract text from PDFs in knowledge/."""
    documents = []

    if not KNOWLEDGE_DIR.exists():
        raise FileNotFoundError(
            "The knowledge folder does not exist."
        )

    for path in sorted(KNOWLEDGE_DIR.iterdir()):
        if path.suffix.lower() == ".txt":
            text = path.read_text(encoding="utf-8").strip()

            if text:
                documents.append({
                    "source": path.name,
                    "text": text,
                })

        elif path.suffix.lower() == ".pdf":
            import pymupdf

            with pymupdf.open(path) as pdf:
                text = "\n".join(
                    page.get_text() for page in pdf
                ).strip()

            if text:
                documents.append({
                    "source": path.name,
                    "text": text,
                })

    return documents


def split_into_chunks(text, chunk_size=120, overlap=25):
    """Split topic-based text into overlapping word chunks."""
    if not isinstance(text, str):
        raise TypeError("text must be a string.")

    if not isinstance(chunk_size, int) or isinstance(chunk_size, bool):
        raise ValueError("chunk_size must be a positive integer.")

    if not isinstance(overlap, int) or isinstance(overlap, bool):
        raise ValueError("overlap must be a non-negative integer.")

    if chunk_size < 1:
        raise ValueError("chunk_size must be at least 1.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be at least 0 and smaller than chunk_size."
        )

    sections = re.split(r"(?m)(?=^TOPIC:\s*)", text)
    chunks = []

    for section in sections:
        section = section.strip()

        if not section:
            continue

        words = section.split()
        start = 0

        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunks.append(" ".join(words[start:end]))

            if end == len(words):
                break

            start = end - overlap

    return chunks


def _get_index_signature():
    """Identify knowledge files and their modification times."""
    if not KNOWLEDGE_DIR.exists():
        raise FileNotFoundError(
            "The knowledge folder does not exist."
        )

    return tuple(
        (path.name, path.stat().st_mtime_ns, path.stat().st_size)
        for path in sorted(KNOWLEDGE_DIR.iterdir())
        if path.is_file()
        and path.suffix.lower() in {".txt", ".pdf"}
    )


def build_index():
    """Build or reuse the TF-IDF index for the knowledge files."""
    global _INDEX_CACHE, _INDEX_CACHE_SIGNATURE

    signature = _get_index_signature()

    if (
        _INDEX_CACHE is not None
        and signature == _INDEX_CACHE_SIGNATURE
    ):
        return _INDEX_CACHE

    documents = load_knowledge()
    chunks = []

    for document in documents:
        for chunk in split_into_chunks(document["text"]):
            chunks.append({
                "source": document["source"],
                "text": chunk,
            })

    if not chunks:
        raise ValueError(
            "No knowledge documents found. Add a non-empty "
            "text or PDF file to the knowledge folder."
        )

    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        stop_words="english",
    )

    matrix = vectorizer.fit_transform(
        [chunk["text"] for chunk in chunks]
    )

    _INDEX_CACHE = (vectorizer, matrix, chunks)
    _INDEX_CACHE_SIGNATURE = signature

    return _INDEX_CACHE


def retrieve(
    query,
    vectorizer,
    matrix,
    chunks,
    top_k=3,
    min_score=0.0,
):
    """Retrieve ranked knowledge chunks with source attribution."""
    if not isinstance(query, str):
        raise TypeError("query must be a string.")

    if not query.strip():
        return []

    if not isinstance(top_k, int) or isinstance(top_k, bool):
        raise ValueError("top_k must be a non-negative integer.")

    if top_k < 0:
        raise ValueError("top_k must be non-negative.")

    if top_k == 0:
        return []

    if (
        not isinstance(min_score, (int, float))
        or isinstance(min_score, bool)
        or not 0.0 <= min_score <= 1.0
    ):
        raise ValueError("min_score must be between 0.0 and 1.0.")

    query_vector = vectorizer.transform([query])
    scores = cosine_similarity(query_vector, matrix).ravel()
    ranked_indices = scores.argsort()[::-1]

    results = []

    for index in ranked_indices:
        score = float(scores[index])

        # Ignore zero-overlap and below-threshold passages.
        if score <= 0 or score < min_score:
            continue

        results.append({
            "source": chunks[index]["source"],
            "text": chunks[index]["text"],
            "score": round(score, 3),
        })

        if len(results) >= top_k:
            break

    return results
