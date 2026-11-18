import unittest
from clinical.reviewer_reliability import cohen_kappa, fleiss_kappa, reliability_report
from clinical.human_adjudication import make_review

class ReliabilityTests(unittest.TestCase):
    def test_cohen_perfect_balanced(self):
        left = {"a":"supported","b":"contradicted"}
        self.assertEqual(cohen_kappa(left,left)["kappa"], 1.0)

    def test_cohen_complete_disagreement(self):
        left = {"a":"supported","b":"contradicted"}
        right = {"a":"contradicted","b":"supported"}
        self.assertEqual(cohen_kappa(left,right)["kappa"], -1.0)

    def test_cohen_no_overlap(self):
        self.assertIsNone(cohen_kappa({"a":"supported"},{"b":"supported"})["kappa"])

    def test_cohen_single_label_undefined(self):
        self.assertIsNone(cohen_kappa({"a":"supported"},{"a":"supported"})["kappa"])

    def test_fleiss_perfect_balanced(self):
        result = fleiss_kappa({"a":("supported","supported"),
                               "b":("contradicted","contradicted")})
        self.assertEqual(result["kappa"], 1.0)

    def test_fleiss_unequal_raters_undefined(self):
        self.assertIsNone(fleiss_kappa({"a":("supported","supported"),
                                         "b":("supported","supported","supported")})["kappa"])

    def test_fleiss_empty(self):
        self.assertIsNone(fleiss_kappa({})["kappa"])

    def test_reliability_report(self):
        reviews = (make_review("negation-reversal","r1","contradicted"),
                   make_review("negation-reversal","r2","supported"))
        result = reliability_report(reviews)
        self.assertEqual(result["categories"]["negation"]["disputed"], 1)
        self.assertEqual(result["reviewer_count"], 2)

if __name__ == "__main__":
    unittest.main()
