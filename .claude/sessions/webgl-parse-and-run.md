In this task we want to developer in the webgl the ability to text algoritm and implent them in the cube

Critical is to use FSM and not break the FSM, use agents to review yiur on this, 
i dont want 1000 state bugs

The feature is like this

THe use see in the upper buttns row a nice keybaod button icon, when it press it enters a programming mode

A editable text box is entred, where use can enter text, the text is in formt understood by algs server

when entring the dev mode, the server is asked to take a snapshot or some other mecanm of the all operatons played on the cube
like in the wiht qyery mode support by the operator, some way to return to prevouse state if needed
we called it "the intial state"

on each key strock the text in the box is sent to sevr for parsing, if error return the text box is sourned or become red
other wise a green
there is a button play, when press we return to the intial state without animation and play the algorithm, of cousre play is disabled 
if parser retrun error, so it is good idea to make the play button gree/red acording to it instead of maybe make all the text box red/green
why we need to retunr to intial state ? becuase user fix the alg and he want to the effective alg on the intial state

if user press cancel then we returnn to itital state and dismiss the box but remebring the text in it
if we press ok then we play and dismissm in this case we play with animation , so the ok must be also red/green
again when playing always from initial state, if user press aplly then it become the inital state
so we have 4 buttons play apply cancel and ok, hope they can enter the phone screen
it can cover the bottom buttons and status

plan , make sure every thing is clear
