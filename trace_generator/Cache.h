#ifndef _CACHE_H
#define _CACHE_H

#include <vector>
#include <string>

class Cache
{
public:    
    enum HitLocation {
	L1,
	L2,
	CPU_L2,
	L3,
	DRAM
    };

    HitLocation access(void *line);
    HitLocation access(void *base, unsigned size);

    static std::string accessesToString(const std::vector<HitLocation> &accesses);
};

#endif
