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
        ## Some of the tests skip none Slice M
        same above
--------------------------------

        fidx = 2 #random.randint(0, ) ✅
        ## Some of the tests skip none Slice M
        same above

--------------------------------

        fidx = 3 #random.randint(0, ) ❌
        ## Some of the tests skip none Slice M
        same above

--------------------------------

        fidx = 3 #random.randint(0, ) ✅
        
        if slice_name is SliceName.M:
            if current_face is cube.back:
                current_index = inv(current_index)
        elif slice_name is SliceName.S:
            if current_face in [cube.down, cube.left]:
                current_index = inv(current_index)
        ## Some of the tests skip none Slice M

==========================================  ✅
# Now tests tests all lsices axi name

    fidx = 0 #random.randint(0, ) ✅
    fidx = 1 #random.randint(0, ) ✅
    fidx = 2 #random.randint(0, ) ✅
    fidx = 3 #random.randint(0, ) ✅
    

=== trying random=========================  ✅

        fidx = random.randint(0, 3) ‼️‼️‼️
        This means results are consistence

=========== disabling claude patch ❌ still fails
        if True:
            rotation_edges = cube.layout.get_face_edge_rotation_cw(rotation_face)
        else:
            # claude code don't understand why it works
            if use_clockwise:
                # Clockwise: top, right, bottom, left
                rotation_edges = [rotation_face.edge_top, rotation_face.edge_right,
                                 rotation_face.edge_bottom, rotation_face.edge_left]
            else:
                # Counter-clockwise: right, top, left, bottom
                rotation_edges = [rotation_face.edge_right, rotation_face.edge_top,
                                 rotation_face.edge_left, rotation_face.edge_bottom]

================== Current status 
        with two patches
        if True:
            rotation_edges = cube.layout.get_face_edge_rotation_cw(rotation_face)
        else:
            # claude code don't understand why it works
            if use_clockwise:
                # Clockwise: top, right, bottom, left
                rotation_edges = [rotation_face.edge_top, rotation_face.edge_right,
                                 rotation_face.edge_bottom, rotation_face.edge_left]
            else:
                # Counter-clockwise: right, top, left, bottom
                rotation_edges = [rotation_face.edge_right, rotation_face.edge_top,
                                 rotation_face.edge_left, rotation_face.edge_bottom]


        if True:
            if slice_name is SliceName.M:
                if current_face is cube.back:
                    current_index = inv(current_index)
            elif slice_name is SliceName.S:
                if current_face in [cube.down, cube.left]:
                    current_index = inv(current_index)

#==============Current status
    replace my patch the second with a logic to find the closed index to rotating image
    
```python
        if True:

            # claude: better explain this: current index nust be close to the rotating image, this is the definition
            #  of rotating over Face, it is the direction and where slice index begin
            shared_with_rotating: Edge = current_face.get_shared_edge(rotation_face)

            # ? vertical cross bottom and up ?

            if current_face.is_bottom_or_top(current_edge):
                # my left index 0 is the rotating face ?
                if current_face.edge_left is shared_with_rotating:
                    ...
                else:
                    current_index = inv(current_index)
            else:  # horizontal cross columns
                # is my bottom index 0 is shared
                if current_face.edge_bottom is shared_with_rotating:
                    ...
                else:
                    current_index = inv(current_index)

```
