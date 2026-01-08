=== M slice ===
fidx = 0 #random.randint(1, 1) ✅
Rotation face: L
Cycle faces: ['F', 'U', 'B', 'D']
First two faces: F, U
Shared edge = Starting edge: FU
Starting face: F
Starting slice index: 0, 0

===========================

=== M slice ===

fidx = 1 #random.randint(1, 1)

Rotation face: L
Cycle faces: ['F', 'U', 'B', 'D']
First two faces: U, B
Shared edge = Starting edge: BU
Starting face: U  ✅  
Starting slice index: 0, 0

======================================

Failing - pick wrong index
tests fail

fidx = 2 #random.randint(1, 1)
        first_face = cycle_faces_ordered[fidx]


=== M slice ===
Rotation face: L
Cycle faces: ['F', 'U', 'B', 'D']
First two faces: B, D
Shared edge = Starting edge: BD
Starting face: B  ❌


if im doing

   if current_face is cube.back:
            current_index = inv(current_index)
   
for M only !!!
  pick the right slice (cube live)
  all M tests passed  tests/geometry/test_face2face_translator.py

=================

=== M slice ===

fidx = 3 #random.randint(1, 1)

Rotation face: L
Cycle faces: ['F', 'U', 'B', 'D']
First two faces: U, B
Shared edge = Starting edge: BU
Starting face: U ✅

============== Trying random ❌

fidx = random.randint(0, 3)


Also for whole
    if result.whole_cube_base_alg.axis_name not in [AxisName.X]:
        return


✅Ignoring all non X and M pass tests/geometry/test_face2face_translator.py