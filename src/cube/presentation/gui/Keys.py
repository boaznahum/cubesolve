"""Backend-independent key constants."""


class Keys:
    """Backend-independent key constants.

    These are abstract key codes that each backend maps to/from
    its native key codes.
    """

    # Letters (using ASCII-like values for convenience)
    A, B, C, D, E, F = 65, 66, 67, 68, 69, 70
    G, H, I, J, K, L = 71, 72, 73, 74, 75, 76  # noqa: E741 TODO: fix
    M, N, O, P, Q, R = 77, 78, 79, 80, 81, 82  # noqa: E741 TODO: fix
    S, T, U, V, W, X = 83, 84, 85, 86, 87, 88
    Y, Z = 89, 90

    # Numbers
    _0, _1, _2, _3, _4 = 48, 49, 50, 51, 52
    _5, _6, _7, _8, _9 = 53, 54, 55, 56, 57

    # Special keys
    ESCAPE = 256
    SPACE = 32
    RETURN = 257
    ENTER = 257  # Alias for RETURN
    TAB = 258
    BACKSPACE = 259
    DELETE = 260
    INSERT = 261

    # Arrow keys
    LEFT = 262
    RIGHT = 263
    UP = 264
    DOWN = 265

    # Function keys
    F1, F2, F3, F4 = 290, 291, 292, 293
    F5, F6, F7, F8 = 294, 295, 296, 297
    F9, F10, F11, F12 = 298, 299, 300, 301

    # Other common keys
    HOME = 268
    END = 269
    PAGE_UP = 270
    PAGE_DOWN = 271

    # Punctuation (commonly used in cube notation)
    GRAVE = 96  # '`' - backtick/grave accent (left of 1)
    SLASH = 47  # '/' - often used for solve command
    QUESTION = 47  # Same as slash (shift+/)
    APOSTROPHE = 39  # "'" - prime moves
    MINUS = 45
    PLUS = 43
    EQUAL = 61
    COMMA = 44
    PERIOD = 46
    BACKSLASH = 92
    BRACKETLEFT = 91  # '['
    BRACKETRIGHT = 93  # ']'

    # Numpad keys
    NUM_ADD = 334  # Numpad +
    NUM_SUBTRACT = 333  # Numpad -
    NUM_0 = 320
    NUM_1 = 321
    NUM_2 = 322
    NUM_3 = 323
    NUM_4 = 324
    NUM_5 = 325
    NUM_6 = 326
    NUM_7 = 327
    NUM_8 = 328
    NUM_9 = 329

    # Modifier keys (for range checking)
    LSHIFT = 340
    RSHIFT = 344
    LCTRL = 341
    RCTRL = 345
    LALT = 342
    RALT = 346
    LMETA = 343  # Left command/super
    RMETA = 347  # Right command/super
