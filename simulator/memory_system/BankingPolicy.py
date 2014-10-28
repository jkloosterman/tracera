import math

# Classes that compute the bank for an address
class BankingPolicyConsecutive(object):
    def __init__(self, num_banks, associativity, line_size):
        assert(self.is_power2(num_banks))
        assert(self.is_power2(associativity))
        assert(self.is_power2(line_size))

        self.num_banks = num_banks
        self.set_bits = int(math.log(associativity, 2))
        self.line_bits = int(math.log(line_size, 2))

    # From http://code.activestate.com/recipes/577514-chek-if-a-number-is-a-power-of-two/
    def is_power2(self, num):
        return num != 0 and ((num & (num - 1)) == 0)

    def bank(self, line):
        line >>= self.line_bits + self.set_bits
        return line & (self.num_banks - 1)
