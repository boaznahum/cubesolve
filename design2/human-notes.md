# Human Notes - OpenGL Model Documentation Project

This file contains background information and instructions from the human developer.

---

## Background

Under design2 we start a huge project of documentation of the cube solve project. The goals are:
- Full understanding and documentation of the model and presentation layer
- Consistency between design2 documents and docstrings in the code (bidirectional)
- Full graphic diagrams of any aspect I request
- Any change in code should be reflected here
- Any change requires my confirmation

## Instructions to Claude

- The instructions here are not in particular order

- You are allowed to change this file for better formatting and English improvement if needed. Ask for clarification if unclear. See state mechanism below.

- You need to develop and construct a state mechanism to work on the documentation task (from now: "this task")

- The state mechanism should support:
  - End Claude session at any step and next session knows exactly how to continue. If needed, consult on how to do it.
  - Not repeat tasks if input was not changed (for example, reformatting this file as described below)
  - Details on what should be done, what should still be investigated
  - Whenever you get or learn new instructions, you should memorize it in a file in the state area
  - All output goes into design2 folder (a.k.a. this folder) or docstrings in code
  - All your internal state (things you learn and the mechanism you develop) should be in `.state` folder under this folder
  - All internal state must be git-controlled files to fulfill the rule that new session can start

- Ask me if something is not clear

### Instructions About Documents

There are few areas of documentation that you must keep consistent - this is the most important rule. I don't need to ask you again and again to align them:
1. The code
2. The docstrings in the code (also the ones I wrote in the past)
3. The documents you create in this folder
4. Your internal state where you keep your insights

**⚠️ CRITICAL: Never document without updating docstrings!**

Every documentation change requires updating ALL FOUR areas:

| Step | Action |
|------|--------|
| 1 | Update/create `design2/*.md` documentation |
| 2 | Update Python docstrings in source files |
| 3 | Add `See: design2/xxx.md` references in docstrings |
| 4 | Update `.state/insights.md` with new learnings |

Docstrings must include:
- Clear explanation of the concept
- Reference to visual documentation: `See: design2/model-id-system.md`
- Correct file paths: `../src/cube/domain/model/`

It will be great if you can put clickable links between documents and docstrings.

Use best agents to understand the model code and later the presentation. If you are not sure, ask me.

If you need more instructions you can ask and add them here.

## Key Concepts to Document

I want to start from the model, then solvers, and then to the presentation layers.

Pay focus on understanding that the cube solution has two phases:
- A big cube where the part slices are important
- Then it becomes a 3x3 cube (reduction) when the parts in the model become the input to the solver

*(Note: Some part methods are useless before reduction - e.g., part color is undefined until all slices are in place)*

Focus on the position and color IDs - things like this.

Understand the role of them when rotating slices and faces, how color IDs play a role.

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

*This file is maintained by the human developer to guide the documentation effort. See comment above about what Claude is allowed to change.*
