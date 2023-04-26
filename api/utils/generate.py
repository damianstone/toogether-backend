import string
import random


def generate_group_code():
    alphabet = string.ascii_uppercase
    letters = "".join(random.choice(alphabet) for i in range(3))
    digits = "".join(random.choice(string.digits) for i in range(3))
    group_code = letters + digits
    return group_code
