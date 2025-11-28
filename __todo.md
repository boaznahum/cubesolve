make sure all test_gui run with all backends, for this we need an absract mechanism
  of key sequences that somehow alternated to the keys that the backend understand
the backend will a pytest fixture, the default should be all meaning all backends

investigate pyopengltk as alternative to pure Canvas rendering for tkinter backend
  - would allow reusing OpenGL code from pyglet backend
  - true 3D rendering instead of 2D isometric projection
  - adds external dependency (pip install pyopengltk)