#ifndef _TRACERA_H
#define _TRACERA_H

/*
 * Use these functions to annotate loops of interest in
 *  an application like so:
 *
 *  _startLoop(UNIQUE_ID);
 *  for (int i = 0; i < MAX; i++)
 *  {
 *     _loopHeader(UNIQUE_ID);
 *     do_work();
 *  }
 *  _endLoop(UNIQUE_ID);
 */

void _startLoop(int staticId);
void _endLoop(int staticId);
void _loopHeader(int staticId);

#endif
