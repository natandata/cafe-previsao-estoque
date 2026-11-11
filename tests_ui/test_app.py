from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest
class AppTests(unittest.TestCase):
 def test_load_language_and_scenario(self):
  at=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=30).run()
  self.assertEqual(len(at.exception),0)
  self.assertEqual(at.subheader[0].value,'Previsão')
  at.radio[0].set_value("EN").run();self.assertEqual(len(at.exception),0)
  self.assertEqual(at.subheader[0].value,'Forecast')
  at.slider[0].set_value(5);at.slider[1].set_value(3);at.select_slider[0].set_value(.975);at.button[0].click().run();self.assertEqual(len(at.exception),0);self.assertEqual(len(at.metric),3)
if __name__=="__main__":unittest.main()
