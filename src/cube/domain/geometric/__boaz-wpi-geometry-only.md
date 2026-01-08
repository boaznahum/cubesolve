✅
current_index: int = 0  # which slice
        slot: int = 0  # position along slice

        ## Some of the tests skip none Slice M

        if slice_name is SliceName.M:
            if current_face is cube.back:
                current_index = inv(current_index)
        elif slice_name is SliceName.S:
            if current_face in [cube.down]:
                current_index = inv(current_index)

=======================================

        fidx = 1 #random.randint(0, ) ✅
        same above

        fidx = 2 #random.randint(0, ) ✅
        same above