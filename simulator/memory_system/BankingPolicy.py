import math

# Classes that compute the bank for an address
class BankingPolicyConsecutive(object):
    def __init__(self, num_banks, line_size):
        assert(self.is_power2(num_banks))
        assert(self.is_power2(line_size))

        self.bank_bits = int(math.log(num_banks, 2))
        self.line_bits = int(math.log(line_size, 2) - 1)

    # From http://code.activestate.com/recipes/577514-chek-if-a-number-is-a-power-of-two/
    def is_power2(self, num):
        return num != 0 and ((num & (num - 1)) == 0)

    def bank(self, line):
        line >>= self.line_bits
        return line & self.bank_bits
