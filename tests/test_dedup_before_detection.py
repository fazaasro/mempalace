"""Tests for hash-dedup before entity detection.

Before this change, if the user's corpus had byte-identical duplicate files
(common artifact of retroactive-renumbering or auto-save snapshots), those
duplicates inflated token frequencies by N× — pushing shared tokens like
'Python' or 'Paris' above the min_frequency threshold unfairly.

The fix: sha256-hash each file's content as it's read. Skip files whose
hash is already in the seen set. Only unique content contributes to
candidate extraction."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from mempalace.entity_detector import detect_entities


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


class TestDedupBeforeDetection(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="mempalace_dedup_test_"))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def _write(self, name: str, content: str) -> Path:
        p = self.tmp / name
        p.write_text(content, encoding="utf-8")
        return p

    def test_identical_duplicates_count_once(self):
        """Three byte-identical files should contribute token counts ONCE."""
        # Content designed so 'Alice' would hit min_frequency=3 ONLY via duplication
        content = (
            "Alice said hi.\nAlice was here.\nBob replied.\n"
            "One mention of Claude.\n"
        )
        # Three byte-identical copies
        p1 = self._write("f1.txt", content)
        p2 = self._write("f2.txt", content)
        p3 = self._write("f3.txt", content)
        # One genuinely distinct file with one 'Alice' mention
        distinct = self._write("f4.txt", "Alice visited.")
        result = detect_entities([p1, p2, p3, distinct])
        # Without dedup: Alice appears 3×2 + 1 = 7 times, passes freq threshold
        # With dedup: Alice appears 2 + 1 = 3 times (from 1 copy + distinct) — still passes
        # Either way Alice is in candidates. Deeper check: the combined text should
        # NOT triple-count. We check this by counting "Alice" occurrences that the
        # detector saw — via the all_text combined length.
        # The key regression test: Bob appears 1× in content + 0 in distinct = 1 total
        # Without dedup: Bob would appear 3× and might pass freq threshold
        # With dedup: Bob appears 1× < threshold, filtered out
        all_names = (
            {e["name"] for e in result["people"]}
            | {e["name"] for e in result["projects"]}
            | {e["name"] for e in result["uncertain"]}
        )
        self.assertNotIn(
            "Bob", all_names,
            "Bob should be filtered by min_frequency=3 — duplicates should not "
            "push its count from 1 (unique) to 3 (triplicated)."
        )

    def test_distinct_files_all_counted(self):
        """Files with unique content should all contribute."""
        p1 = self._write("a.txt", "Alice said. Alice said. Alice said.\nAlice noted.")
        p2 = self._write("b.txt", "Bob spoke. Bob answered.\nBob agreed.")
        p3 = self._write("c.txt", "Carol asked. Carol waited.\nCarol left.")
        result = detect_entities([p1, p2, p3])
        all_names = (
            {e["name"] for e in result["people"]}
            | {e["name"] for e in result["projects"]}
            | {e["name"] for e in result["uncertain"]}
        )
        # All three names appear 3+ times in their respective files — all should pass
        # frequency threshold regardless of dedup (content was unique).
        self.assertIn("Alice", all_names)
        self.assertIn("Bob", all_names)
        self.assertIn("Carol", all_names)


if __name__ == "__main__":
    unittest.main()
