import math

class BankingPolicy(object):
    # From http://code.activestate.com/recipes/577514-chek-if-a-number-is-a-power-of-two/
    def is_power2(self, num):
        return num != 0 and ((num & (num - 1)) == 0)    

# Classes that compute the bank for an address
class BankingPolicyConsecutive(BankingPolicy):
    def __init__(self, num_banks, line_size):
        assert(self.is_power2(num_banks))
        assert(self.is_power2(line_size))

        self.num_banks = num_banks
        self.line_bits = int(math.log(line_size, 2))
        self.bank_bits = int(math.log(num_banks, 2))

    def bank(self, line):
        return (line >> self.line_bits) & (self.num_banks - 1)

    def set(self, line):
        return line >> (self.line_bits + self.bank_bits)

class BankingPolicyPrime(BankingPolicy):
    def __init__(self, num_banks, line_size):
        assert(not self.is_power2(num_banks))
        assert(self.is_power2(line_size))

        self.num_banks = num_banks
        self.line_bits = int(math.log(line_size, 2))

    def bank(self, line):
        return (line >> self.line_bits) % self.num_banks

    def set(self, line):
        return (line >> self.line_bits) / self.num_banks

class BankingPolicySkew(BankingPolicy):
    def __init__(self, num_banks, line_size):
        assert(self.is_power2(num_banks))
        assert(self.is_power2(line_size))

        self.num_banks = num_banks
        self.line_bits = int(math.log(line_size, 2))
        self.bank_bits = int(math.log(num_banks, 2))

    def bank(self, line):
        a = (line >> self.line_bits)
        r = a / self.num_banks
        skew = r % self.num_banks
        bank = (a + skew) % self.num_banks
        return bank

    def set(self, line):
        return (line >> self.line_bits) / self.num_banks
