Please learn the multi-line parser.
I want you to be a compiler-writer expert.
Make a multi-line parser that understands expressions like:

$setup = X Y L R

```
$setup

U R L

$setup'
```

This will run the setup algorithm, then U L R, and then the prime (inverse) of setup.

Also this is supported:

```
$I = 1

[$I:$I+1]M2
```

is equivalent to

```
[1:2]M2
```

This is also supported:

```
$n = 5

$corner = R' D' R D

$corner * $n
```

Perform $corner 5 times.

Make sure the WebGL dev panel (when user presses the keyboard icon) supports it.
Make sure `cubesolve/src/cube/resources/algs` files that are executed via pyglet F1..F5 are supported.

Add tests to `tests/parsing`.

Plan and implement — make me happy!
