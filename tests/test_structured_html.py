import unittest
from clinical.structured_html import extract_structured_text

class StructuredHTMLTests(unittest.TestCase):
    def test_heading_and_paragraph(self):
        text = extract_structured_text("<main><h2>Monitoring</h2><p>Synthetic guidance.</p></main>")
        self.assertIn("## Monitoring", text)
        self.assertIn("Synthetic guidance.", text)

    def test_table_rows_retained(self):
        text = extract_structured_text("<table><tr><th>Drug</th><th>Note</th></tr><tr><td>Fictional A</td><td>Review</td></tr></table>")
        self.assertIn("[TABLE]", text)
        self.assertIn("Drug | Note", text)
        self.assertIn("Fictional A | Review", text)
        self.assertIn("[/TABLE]", text)

    def test_superscript_footnote_marker(self):
        text = extract_structured_text("<p>Statement<sup>1</sup></p><p>1. Synthetic footnote</p>")
        self.assertIn("Statement1", text)
        self.assertIn("Synthetic footnote", text)

    def test_skip_scripts(self):
        text = extract_structured_text("<script>bad()</script><p>Safe</p>")
        self.assertNotIn("bad()", text)
        self.assertIn("Safe", text)

    def test_no_remote_fetch(self):
        self.assertEqual(extract_structured_text("<p>Offline only</p>"), "Offline only")

if __name__ == "__main__":
    unittest.main()
