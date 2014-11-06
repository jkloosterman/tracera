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

    def bank(self, line):
        return (line >> self.line_bits) & (self.num_banks - 1)

# Hash the set and tag bits to map to a bank.
# But then which bits should the cache use?
# http://mprc.pku.cn/mentors/training/ISCAreading/1993/p337-gao/p337-gao.pdf
#
#  p = number of banks
#  d = logical address
#  physical address (u,v): u-th word in v-th bank
#  v = d mod p
#  u = left l' bits of d = d mod m
#  Module has m = 2^l' words
#
# My interpretation:
#    [tag|set|offset] -> like we had no banks.
# We do [tag|set] mod (# banks) to find the bank.
class BankingPolicyChineseRemainder(BankingPolicy):
    def __init__(self, num_banks, line_size):
        assert(self.is_power2(line_size))
        assert(not self.is_power2(num_banks))

        self.num_banks = num_banks
        self.line_bits = int(math.log(line_size, 2))

    def bank(self, line):
        return (line >> self.line_bits) % self.num_banks
