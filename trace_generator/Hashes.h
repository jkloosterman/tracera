#ifndef _HASHES_H
#define _HASHES_H

#include "Tracer.h"
#include "Cache.h"

namespace std
{
    template<>
    struct hash<vector<TraceNode> > {
	size_t operator() (const std::vector<TraceNode> &trace) const {
	    size_t sum = 0;
	    size_t product = 1;
	    
	    for (unsigned i = 0; i < trace.size(); i++)
	    {
		const TraceNode &t = trace[i];

		// this is naughty because bbId will catch the other members
		//  of the union too.
		sum += t.bbId + 1;
		product *= t.bbId + 1;
	    }
	    
	    return sum ^ product;
	}
    };

    template<>
    struct hash<vector<unsigned> > {
	size_t operator() (const std::vector<unsigned> &v) const {
	    size_t sum = 0;
	    size_t product = 1;
	    
	    for (unsigned i = 0; i < v.size(); i++)
	    {
		unsigned val = v[i] + 1;
		sum += val;
		product *= val;
	    }

	    return sum ^ product;
	}
    };

    template<>
    struct hash<vector<int> > {
	size_t operator() (const std::vector<int> &v) const {
	    size_t sum = 0;
	    size_t product = 1;
	    
	    for (unsigned i = 0; i < v.size(); i++)
	    {
		int val = v[i] + 1;
		sum += val;
		product *= val;
	    }

	    return sum ^ product;
	}
    };

    template<>
    struct hash<vector<void *> > {
	size_t operator() (const std::vector<void *> &v) const {
	    size_t sum = 0;
	    size_t product = 1;
	    
	    for (unsigned i = 0; i < v.size(); i++)
	    {
		unsigned long val = (unsigned long) v[i] + 1;
		sum += val;
		product *= val;
	    }

	    return sum ^ product;
	}
    };

    template<>
    struct hash<vector<pair<int, unsigned> > > {
	size_t operator() (const std::vector<pair<int, unsigned>> &v) const {
	    size_t sum = 0;
	    size_t product = 1;
	    
	    for (unsigned i = 0; i < v.size(); i++)
	    {
		sum += v[i].first + v[i].second;

                // this is used for some vectors whose first element has v[i].first = 0;
		product *= v[i].first + v[i].second + 1;
	    }

	    return sum ^ product;
	}
    };

    template<>
    struct hash<vector<pair<int, void *> > > {
	size_t operator() (const std::vector<pair<int, void *>> &v) const {
	    size_t sum = 0;
	    size_t product = 1;
	    
	    for (unsigned i = 0; i < v.size(); i++)
	    {
		sum += v[i].first + (long) v[i].second;
		product *= (v[i].first + 1) * ((long) v[i].second + 1);
	    }

	    return sum ^ product;
	}
    };	

    template<>
    struct hash<MemoryTrace> {
	size_t operator() (const MemoryTrace &mt) const {
	    return mt.hash();
	}
    };
/*
    template<>
    struct hash<vector<Cache::HitLocation> > {
	size_t operator() (const std::vector<Cache::HitLocation> &v) const {
	    size_t sum = 0;
	    size_t product = 1;

	    for(unsigned i = 0; i < v.size(); i++)
	    {
		unsigned val = v[i];
		sum += val;
		product *= val;
	    }

	    return sum ^ product;
	}
    };
*/

/*
    template<>
    struct hash<vector<pair<unsigned, unsigned> > > {
	size_t operator() (const vector<pair<unsigned, unsigned> > &v) const {
            size_t sum = 0;
            size_t product = 0;

            for (unsigned i = 0; i < v.size(); i++)
            { 
                sum += v[i].first + v[i].second;
                product *= v[i].first * v[i].second;
            }
	    
            return sum ^ product;
	}
    };
*/

    template<>
    struct hash<pair<unsigned, unsigned> > {
	size_t operator() (pair<unsigned, unsigned> p) const {
	    hash<unsigned> h;
	    return h(p.first) ^ h(p.second);
	}
    };
}


#endif
