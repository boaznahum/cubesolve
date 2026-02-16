1. Why _LBLNxNCenters cannot use commutator search method ✅
   RESOLVED: _LBLNxNCenters uses a target-first approach (iterate unsolved target positions,
   search source via rotation) which is equivalent to NxNCenters's source-first approach
   (search_big_block + _block_commutator) for row-constrained solving. Both find the same
   1×N blocks, but target-first is more efficient (searches K unsolved positions in one row
   vs M matching positions on entire source face). Additionally, NxNCenters's code cannot be
   reused directly because: (a) _point_on_source() is hardcoded for front↔up/back face pairs,
   (b) _block_commutator() lacks marker protection (s2 validation), (c) search_big_block finds
   multi-row blocks invalid for LBL's row-by-row constraint. No code changes needed.
2. slice optimization, we dont need to protect even middle slices, faces holder preserve context will do it
    yes, but it confuse edges from some reason, simple gui demonstration shows it, need to investigate ❌
3. Face marker cache ✅
4. Faces holder  restore need to be smart  that the previous is ok ✅
5. Face tracer search piece  too much printing ✅