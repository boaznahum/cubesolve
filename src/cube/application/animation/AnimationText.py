class _TextRecord:

    def __init__(self, h1, h2, h3) -> None:
        super().__init__()
        self.heads = (h1, h2, h3)


class AnimationText:

    def __init__(self) -> None:
        super().__init__()
        self._stack: list[_TextRecord] = []

    @property
    def h1(self):
        return "This is line 1"

    @property
    def h2(self):
        return "This is line 2"

    @property
    def h3(self):
        return "This is line 3"

    def get_line(self, i) -> str | None:

        stack = self._stack
        if not stack:
            return None

        return stack[len(stack) - 1].heads[i]

    def push_heads(self, h1=None, h2=None, h3=None):
        """

        :param h1: if not none then h1, h2, h3 are replaced on top of stack, otherwise
        :param h2: if not none h2, h3 are replaced on top of stack, otherwise
        :param h3: if not none h3 is replaced on top of stack
        :return:
        """

        def replace(prev, new: str | None) -> str:
            if new is None:
                return prev

            new = new.strip()

            if prev is None:
                if new.startswith("/"):
                    return new[1:]
                elif new.startswith("+"):
                    return new[1:]
                if new.startswith(", "):
                    return new[1:].strip()
                else:
                    return new

            if new.startswith("/"):
                return new[1:]  # replace
            elif new.startswith("+"):
                return prev + " " + new[1:]
            if new.startswith(", "):
                return prev + new  # no need for space
            else:
                return prev + ",  " + new

        stack = self._stack
        if stack:
            top = stack[len(stack) - 1]
            heads = top.heads
            th1 = heads[0]
            th2 = heads[1]
            th3 = heads[2]
        else:
            th1 = None
            th2 = None
            th3 = None

        if h1 is not None:  # "" also replace all
            th1 = replace(th1, h1)
            th2 = replace(th2, h2)  # might be None
            th3 = h3  # # might be None
        elif h2 is not None:
            th2 = replace(th2, h2)
            th3 = h3
        elif h3 is not None:
            th3 = h3

        top = _TextRecord(th1, th2, th3)
        stack.append(top)

    def pop_heads(self):

        assert self._stack
        self._stack.pop()
