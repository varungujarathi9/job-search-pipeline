import unittest

from pipeline.dedupe import dedupe_postings
from pipeline.postings import Posting


def _posting(external_id: str, source: str = "greenhouse") -> Posting:
    return Posting(
        source=source,
        company="Example Co",
        board_token="examplecorp",
        external_id=external_id,
        title="Senior Backend Engineer",
        location="Denver, CO",
        url=f"https://example.com/job/{external_id}",
        description="",
        posted_at=None,
    )


class TestDedupe(unittest.TestCase):
    def test_no_seen_keys_returns_all_as_new(self):
        postings = [_posting("1"), _posting("2")]
        new, seen = dedupe_postings(postings, set())
        self.assertEqual(len(new), 2)
        self.assertEqual(len(seen), 2)

    def test_previously_seen_posting_is_dropped(self):
        postings = [_posting("1"), _posting("2")]
        seen_keys = {postings[0].dedupe_key}
        new, updated = dedupe_postings(postings, seen_keys)
        self.assertEqual(len(new), 1)
        self.assertEqual(new[0].external_id, "2")
        self.assertEqual(len(updated), 2)

    def test_duplicate_within_same_batch_is_collapsed(self):
        postings = [_posting("1"), _posting("1"), _posting("2")]
        new, updated = dedupe_postings(postings, set())
        self.assertEqual(len(new), 2)
        self.assertEqual({p.external_id for p in new}, {"1", "2"})


if __name__ == "__main__":
    unittest.main()
