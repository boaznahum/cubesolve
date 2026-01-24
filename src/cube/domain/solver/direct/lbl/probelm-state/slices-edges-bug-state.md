# The bug

1. 5x5
2. Reset
3. Scramble 0
4. Solve instant ,midlle slcies centers, centers are diabled _lbl_config.py BIG_LBL_RESOLVE_CENTER_SLICES=False

state after solving, all edges except one:
![img.png](img.png)

this is happens also with animation ~~~ (fast on new machine, also on my other)

# New insight !!!

if i first solve L1 and only then slice centres that it works !!!
In the past I thought it is related to working with/without animation

so what is the diffrent ? one diffrent that we create trackers twice,
so i added a patch:
```python
        # A patch to test my assumption on bug of edges
        if what == SolveStep.LBL_SLICES_CTR:
            # do it with two separated trackers

            # it i wll be called agin in the loop in case of parity detection
            _common.clear_all_type_of_markers(self.cube)

            with FacesTrackerHolder(self) as th:
                self._solve_layer1_centers(th)
                self._solve_layer1_edges(th)
                self._solve_layer1_corners(th)

            with FacesTrackerHolder(self) as th:
                self._solve_face_rows(th)

            return sr

```
