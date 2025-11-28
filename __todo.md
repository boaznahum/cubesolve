make sure all test_gui run with all backends, for this we need an absract mechanism
  of key sequences that somehow alternated to the keys that the backend understand
the backend will a pytest fixture, the default should be all meaning all backends