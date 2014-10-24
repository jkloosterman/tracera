#include "BBInstructions.h"
#include "Database.h"
#include <cassert>
#include <iostream>
using namespace std;

BBInstructions::BBInstructions(Database &_database)
    : database(_database)
{
    curBB = -1;
}

void BBInstructions::startBB(int bbId)
{
    curBB = bbId;
}

void BBInstructions::endBB()
{
    assert(curBB >= 0);
    database.registerBB(curBB, curInstructions);
    curInstructions.clear();
}

void BBInstructions::addInstruction(INS ins)
{
    BBInstruction type = classifyInstruction(ins);
    curInstructions.push_back(type);
}

void BBInstructions::addLoad()
{
    curInstructions.push_back(BBInstruction::LOAD);
}

void BBInstructions::addStore()
{
    curInstructions.push_back(BBInstruction::STORE);
}

BBInstructions::BBInstruction BBInstructions::classifyInstruction(INS ins)
{
    CATEGORY category = static_cast<CATEGORY>(INS_Category(ins));
    assert(category != XED_CATEGORY_INVALID);

    // See pin/extras/xed2-ia32/include/xed-category-enum.h
    //  for categories.
    // There are no explicit memory instructions because x86
    //  doesn't use them.
    switch (category)
    {
    case XED_CATEGORY_X87_ALU:
    case XED_CATEGORY_VFMA:
    case XED_CATEGORY_FMA4:
    case XED_CATEGORY_FCMOV:
	// fall through

    case XED_CATEGORY_3DNOW:
    case XED_CATEGORY_AVX:
    case XED_CATEGORY_AVX2:
    case XED_CATEGORY_AVX2GATHER:
    case XED_CATEGORY_SSE:
    case XED_CATEGORY_MMX:
	// This is a hack, but based on experience we can assume
	//  floating-point is done with MMX in x86_64.
	// There's just a gotcha that we have to be careful no
	//  vectorization happens to input code because we'll miscount.
	//   gcc: -fno-tree-vectorize (https://gcc.gnu.org/projects/tree-ssa/vectorization.html)
	//   clang: -fno-vectorize
	return FP;

    case XED_CATEGORY_CALL:
    case XED_CATEGORY_RET:
    case XED_CATEGORY_SYSCALL:
    case XED_CATEGORY_SYSRET:
    case XED_CATEGORY_SYSTEM:
    case XED_CATEGORY_UNCOND_BR:
	// unconditional control flow goes through integer pipe.
	return INTEGER;

    default:
	return INTEGER;
    }
}
