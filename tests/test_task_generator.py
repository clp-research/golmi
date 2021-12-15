import unittest

from app.dynamatt import dynatasks


class TaskGeneratorTestCase(unittest.TestCase):

    def test_generate_random_sample(self):
        tasks = dynatasks.TaskGenerator.create()
        sample = tasks.generate_random_sample()
        print(sample)
        print(sample["target"].to_dict())

    def test_generate_random_samples(self):
        tasks = dynatasks.TaskGenerator.create()
        for sample in tasks.generate_random_samples(100):
            print(sample["props"])

    def test_generate_random_samples_ncolor_ntypes(self):
        tasks = dynatasks.TaskGenerator.create(n_colors=3, n_types=6)
        for sample in tasks.generate_random_samples(100):
            print(sample["props"])


if __name__ == '__main__':
    unittest.main()
