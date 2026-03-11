from curses import wrapper
import curses

def main(stdscr):
    # Clear screen
    stdscr.clear()

    stdscr.keypad(True)

    # This raises ZeroDivisionError when i == 10.
    for i in range(0, 11):
        v = i + 1
        stdscr.addstr(i, 0, '10 divided by {} is {}'.format(v, 10/v))

    stdscr.refresh()
    while True:
        key = stdscr.getch()
       # stdscr.addstr(11, 0, f'Key is |{key}|, { [ord(c) for c in key ]}')
        stdscr.addstr(11, 0, f'Key is |{key}|')
        if key == curses.KEY_BREAK:
            break

wrapper(main)