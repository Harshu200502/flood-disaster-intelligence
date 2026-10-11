
import unittest

from rag import build_index, retrieve, split_into_chunks


class TestRAG(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.vectorizer, cls.matrix, cls.chunks = build_index()

    def test_flood_safety_retrieval(self):
        results = retrieve(
            "What should people avoid during flooding?",
            self.vectorizer,
            self.matrix,
            self.chunks,
        )
        self.assertTrue(results)
        self.assertIn("Flood Safety", results[0]["text"])
        self.assertIn("source", results[0])
        self.assertGreater(results[0]["score"], 0)

    def test_evacuation_retrieval(self):
        results = retrieve(
            "What should people do during evacuation?",
            self.vectorizer,
            self.matrix,
            self.chunks,
        )
        self.assertTrue(results)
        self.assertIn("Evacuation", results[0]["text"])

    def test_blank_query_returns_empty_list(self):
        results = retrieve(
            "   ",
            self.vectorizer,
            self.matrix,
            self.chunks,
        )
        self.assertEqual(results, [])

    def test_zero_top_k_returns_empty_list(self):
        results = retrieve(
            "flood safety",
            self.vectorizer,
            self.matrix,
            self.chunks,
            top_k=0,
        )
        self.assertEqual(results, [])

    def test_negative_top_k_raises_error(self):
        with self.assertRaises(ValueError):
            retrieve(
                "flood safety",
                self.vectorizer,
                self.matrix,
                self.chunks,
                top_k=-1,
            )

    def test_non_string_query_raises_error(self):
        with self.assertRaises(TypeError):
            retrieve(
                None,
                self.vectorizer,
                self.matrix,
                self.chunks,
            )

    def test_high_threshold_filters_results(self):
        results = retrieve(
            "What should people avoid during flooding?",
            self.vectorizer,
            self.matrix,
            self.chunks,
            min_score=1.0,
        )
        self.assertEqual(results, [])

    def test_invalid_chunk_overlap_raises_error(self):
        with self.assertRaises(ValueError):
            split_into_chunks(
                "sample text",
                chunk_size=5,
                overlap=5,
            )

    def test_index_is_reused(self):
        first = build_index()
        second = build_index()
        self.assertIs(first, second)


if __name__ == "__main__":
    unittest.main(verbosity=2)
