import unittest, emporium

class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        emporium.setup()
        emporium.app.config['TESTING'] = True
        self.app = emporium.app.test_client()

