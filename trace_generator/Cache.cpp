#include "Cache.h"
using namespace std;

Cache::HitLocation Cache::access(void *line)
{
    return HitLocation::DRAM;
}

Cache::HitLocation Cache::access(void *base, unsigned size)
{
    return HitLocation::DRAM;
}

string Cache::accessesToString(const vector<Cache::HitLocation> &accesses)
{
    string s;

    for(unsigned i = 0; i < accesses.size(); i++)
    {
	if (accesses[i] == L1)
	    s += "1";
	else if(accesses[i] == L2)
	    s += "2";
	else if (accesses[i] == CPU_L2)
	    s += "C";
	else if (accesses[i] == L3)
	    s += "3";
	else
	    s += "D";
    }

    return s;
}
