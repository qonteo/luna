import random


class DataGenerator:

    @staticmethod
    def generate_email():
        x = random.randint(0, 1000000)
        y = random.randint(0, 1000000)
        return "{0}@{1}.com".format(x, y)

    @staticmethod
    def generate_org_name():
        return "AutotestTestOrg{0}".format(random.randint(0, 1000000))
