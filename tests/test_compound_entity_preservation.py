"""Tests for compound-name preservation in extract_candidates.

When a multi-word entity like 'Claude Code' appears N times in text, the
candidate list should contain 'Claude Code' with count N — and 'Code' alone
should NOT be inflated by those occurrences (otherwise 'Code' gets classified
as a spurious person because it appears as often as 'Claude Code').

TDD: these tests fail on develop-head because current extract_candidates
counts single-word AND multi-word matches independently, double-counting
'Claude' and 'Code' whenever 'Claude Code' appears together."""
import unittest
from mempalace.entity_detector import extract_candidates


class TestCompoundNamePreservation(unittest.TestCase):

    def test_claude_code_compound_is_kept_atomic(self):
        """'Claude Code' appearing 3+ times should be a compound candidate."""
        text = ("Claude Code is the CLI. " * 4) + " no other context."
        candidates = extract_candidates(text)
        self.assertIn("Claude Code", candidates,
                      "Compound name 'Claude Code' should be extracted as a single candidate")
        self.assertGreaterEqual(candidates["Claude Code"], 3)

    def test_standalone_code_is_deducted_from_compound_occurrences(self):
        """If 'Code' only appears as part of 'Claude Code', the standalone
        'Code' count should NOT inflate the candidate pool. Either 'Code' is
        absent, or its count reflects ONLY occurrences where it was NOT part
        of the compound."""
        text = ("Claude Code is the CLI. " * 4) + " no other context."
        candidates = extract_candidates(text)
        # 'Code' appeared 4 times ONLY as part of 'Claude Code'. It should
        # not be a standalone candidate with count 4.
        if "Code" in candidates:
            self.assertLess(
                candidates["Code"], 4,
                "'Code' count should be reduced by compound-match subtraction; "
                "current regex double-counts, inflating 'Code' to 4.")

    def test_standalone_claude_is_deducted_from_compound_occurrences(self):
        """Same invariant — 'Claude' on its own should not be inflated by
        'Claude Code' compound matches."""
        text = ("Claude Code is the CLI. " * 4) + " no other context."
        candidates = extract_candidates(text)
        if "Claude" in candidates:
            self.assertLess(
                candidates["Claude"], 4,
                "'Claude' count should be reduced by 'Claude Code' compound matches"
            )

    def test_standalone_mention_still_counted(self):
        """If 'Claude' appears WITHOUT 'Code' next to it, that standalone
        occurrence should still be counted normally (need ≥ 3 of each to
        pass the min_frequency filter applied by extract_candidates)."""
        text = (
            "Claude Code is the CLI. " * 3  # 3 compound occurrences
            + "Separately, Claude answered. "
            + "Claude is an AI. "
            + "Claude helps. "  # 3 standalone Claude occurrences
        )
        candidates = extract_candidates(text)
        # Claude Code: 3 occurrences — passes min_frequency=3
        self.assertEqual(candidates.get("Claude Code", 0), 3,
                         "compound 'Claude Code' should count 3 exact matches")
        # Standalone Claude: 3 more (not inside 'Claude Code'); should be
        # counted as 3, NOT 6 (which would double-count the compound occurrences).
        self.assertIn("Claude", candidates,
                      "Claude as standalone should still be a candidate")
        self.assertEqual(candidates["Claude"], 3,
                         "standalone 'Claude' should count 3 — excluding the 3 "
                         "compound occurrences")


if __name__ == "__main__":
    unittest.main()
