"""Why a PR is not advancing: one verdict, fixed order, never the model's."""
import datetime as dt
import unittest

import pr_blockers as B

NOW = dt.datetime(2026, 11, 11, 21, 35, 0, tzinfo=dt.timezone.utc)
HEAD = "03d78d991797f549ca25301ebb5b1d1481392f60"


def check(name, conclusion="SUCCESS", status="COMPLETED", started="2026-11-11T21:23:00Z"):
    return {"name": name, "conclusion": conclusion, "status": status, "startedAt": started}


def pr(**extra):
    base = {"number": 805, "title": "Sound first", "state": "OPEN", "headRefOid": HEAD, "baseRefName": "main",
            "mergeable": "MERGEABLE", "statusCheckRollup": [check("hitl"), check("phase"), check("test_web")]}
    base.update(extra)
    return base


class Verdict(unittest.TestCase):
    def test_signed_and_green_is_ready(self):
        d = B.diagnose(pr(), 0, NOW)
        self.assertEqual((d["verdict"], d["head"], d["number"]), ("READY", HEAD[:12], 805))

    def test_signed_with_a_check_running_waits_and_says_for_how_long(self):
        d = B.diagnose(pr(statusCheckRollup=[check("hitl"), check("phase"),
                                             check("test_web", conclusion="", status="IN_PROGRESS")]), 0, NOW)
        self.assertEqual(d["verdict"], "WAITING_CHECKS")
        self.assertEqual(d["causes"][0]["detail"], "test_web (12 min)")
        self.assertIn("merges by itself", d["next"])

    def test_no_signature_for_this_head(self):
        d = B.diagnose(pr(statusCheckRollup=[check("hitl", "FAILURE"), check("phase"), check("test_web")]), 0, NOW)
        self.assertEqual(d["verdict"], "NEEDS_SIGNATURE")

    def test_the_signature_check_never_counts_as_a_red_check(self):
        d = B.diagnose(pr(statusCheckRollup=[check("hitl", "FAILURE"), check("test_web")]), 0, NOW)
        self.assertNotIn("RED_CHECKS", [c["code"] for c in d["causes"]])

    def test_behind_main_warns_that_the_signature_will_not_follow(self):
        d = B.diagnose(pr(), 2, NOW)
        self.assertEqual(d["verdict"], "BEHIND_MAIN")
        self.assertEqual(d["causes"][0]["detail"], "2 commit(s) behind main")
        self.assertIn("no longer covers", d["next"])

    def test_the_order_is_fixed_conflict_red_behind_signature_waiting(self):
        d = B.diagnose(pr(mergeable="CONFLICTING",
                          statusCheckRollup=[check("hitl", "FAILURE"), check("phase", "FAILURE"),
                                             check("test_web", conclusion="", status="QUEUED", started=None)]),
                       3, NOW, both_touched=["public/counters.json", "config/sw-huella.txt", "public/counters.json"])
        self.assertEqual([c["code"] for c in d["causes"]],
                         ["CONFLICT", "RED_CHECKS", "BEHIND_MAIN", "NEEDS_SIGNATURE", "WAITING_CHECKS"])
        self.assertEqual(d["causes"][0]["detail"], "config/sw-huella.txt, public/counters.json")
        self.assertEqual(d["causes"][4]["detail"], "test_web")

    def test_merged_and_closed_stop_there(self):
        self.assertEqual(B.diagnose(pr(state="MERGED"), None, NOW)["causes"], [{"code": "MERGED", "detail": ""}])
        self.assertEqual(B.diagnose(pr(state="CLOSED"), 4, NOW)["verdict"], "CLOSED")

    def test_missing_facts_are_no_data_never_ready(self):
        self.assertEqual(B.diagnose(None, 0, NOW)["verdict"], "NO_DATA")
        self.assertEqual(B.diagnose({"number": 1}, 0, NOW)["verdict"], "NO_DATA")
        d = B.diagnose(pr(), None, NOW)
        self.assertEqual(d["causes"][-1], {"code": "NO_DATA", "detail": "distance_to_main_not_measured"})

    def test_a_signing_run_in_the_background_is_said(self):
        self.assertIn("do not start another", B.diagnose(pr(), 0, NOW, signing_running=True)["signing"])
        self.assertNotIn("signing", B.diagnose(pr(), 0, NOW))

    def test_same_facts_same_answer(self):
        self.assertEqual(B.diagnose(pr(), 1, NOW), B.diagnose(pr(), 1, NOW))

    def test_a_clock_that_makes_no_sense_gives_no_minutes(self):
        d = B.diagnose(pr(statusCheckRollup=[check("hitl"), check("test_web", "", "IN_PROGRESS", "2027-01-01T00:00:00Z")]), 0, NOW)
        self.assertEqual(d["causes"][0]["detail"], "test_web")


class Words(unittest.TestCase):
    def test_the_line_reads_as_one_sentence(self):
        d = B.diagnose(pr(), 2, NOW)
        self.assertTrue(B.line(d).startswith("#805 · BEHIND_MAIN · 2 commit(s) behind main · Main moved."))

    def test_the_question_fits_the_chat_and_carries_only_facts(self):
        d = B.diagnose(pr(mergeable="CONFLICTING"), 2, NOW, both_touched=["a/" + "x" * 80 + str(i) for i in range(30)])
        q = B.question(d, "T" * 300)
        self.assertLessEqual(len(q), 600)
        self.assertIn("#805", q)
        self.assertIn("CONFLICT", q)
        self.assertIn("Do not invent", B.question(B.diagnose(pr(), 0, NOW), "Sound first"))


if __name__ == "__main__":
    unittest.main()
