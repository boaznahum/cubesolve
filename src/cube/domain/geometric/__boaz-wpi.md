Failing - pick wrong index
tests fail

fidx = 2 #random.randint(1, 1)
        first_face = cycle_faces_ordered[fidx]


=== M slice ===
Rotation face: L
Cycle faces: ['F', 'U', 'B', 'D']
First two faces: B, D
Shared edge = Starting edge: BD
Starting face: B


if im doing

   if current_face is cube.back:
            current_index = inv(current_index)
   
for M only !!!
  pick the right slice (cube live)
  all M tests passed  tests/geometry/test_face2face_translator.py

