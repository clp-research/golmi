import unittest

from scripts.generate_samples import generate_samples


class MyTestCase(unittest.TestCase):

    def test_generate_samples(self):
        generate_samples(1000, output_path=".", store_strategy="single")


if __name__ == '__main__':
    unittest.main()
