# Human Notes - OpenGL Model Documentation Project

This file contains background information and instructions from the human developer.

---

## Background

under design2 we start a huge projrct of doumentation of the cube solve priject, the gial is :
full yndestabdung abd dicumentation of the model and presentation layer.
considtence between design 2 dicuments and doc string in the cide in both direction
full graphjc diagrams id any askect i request.
any change in cide shuuld be rfelccted here.
any change requires my cinfirmation.


## Instructions to claude
- the instrction here are not in particukar otder

- you are allowed to change this file fir better fitmstting snd englush improvement if need ask for clarification. see state mechanidm below

- you need to drvelope snd cistructca state mechsnidm to work on the dicumnets tadk akas from now this task

- the state mrcsnidm shuld support:
-- end clsude session in sny step snd next sesdion know exactly  how ti continue. if need consult againts how to fo it.
-- not repeat tasks if input where not changed gir example tefitmatting this file as described below.
-- details on what shuld be done what shoild still investigate.
-- when rver youvgit or learn new instructiond you dhold mrniruze it in gile in the state areA.
-- all outout  goes  into design  2 folder akas the folder  or dic string in vide
-- all yiur enternsl stAte tukes yku mearn snd ghe mrcanidm you develope shoikd be in .state filder unfer this folder.
. all inernal state must be git controoled fikes to fitfull the tule jf new session can start

- ask me if domething us not clear

indtructuin sbout documents:

there are few  area of documentstion that you mudt keep consist - this is the modt imprying rule, i dont need to adj yih agsin and agsin to align them
1. the code
2. the doc string in the code akdo yhe ones i write in the past
3. the documents you create in thus folder
4. your internal state ehre you keep yiur insights

it will be great if yiu csn put clicksbke links btween documents snd doc stringd

use best agrnts to understabd the modrl cide and katter the presrntstion if you sre bot sure ask me

if you need more instructions you can asked snd add them here

(Add your instructions here)

## Key Concepts to Document

i want to start from the model then solvers and then to thevoresentstion layers

pay focus  if understanding the the cube solituon heve two phasex - a big cube where the part slices are the importnat
egrn it brcome a 3x3 cube - reduction - wgrn the parts in the model us the inlut to the solver.
(Note: some part methods are useless before reduction - e.g., part color is undefined until all slices are in place) 

giucs on the position and cilor ids things line this

underdtsnd the role of them when rotating silces and faces hiw color ids play role

(Add key concepts here)

## The Story: How I Developed the Cube

*(This section captures the developer's design insights and history)*

### Two-Phase Architecture Insight

The cube solution has two distinct phases, and this affects which part methods are meaningful:

**Phase 1 - Big Cube (e.g., 5x5):**
- Focus is on part slices
- Some part methods are useless in this phase
- Example: A part's "color" is NOT defined until all its slices are in place
- Before reduction, a part doesn't have one single color - asking for it is meaningless

**Phase 2 - After Reduction (3x3):**
- The cube is reduced to a 3x3 structure
- Now parts have well-defined colors
- Parts become valid input to the solver

**Key insight:** Certain part properties/methods only make sense in certain phases.

*(More story to be added here)*
---

*This file is maintained by the human developer to guide the documentation effort. but see cooment above what sllwed to be changed*
