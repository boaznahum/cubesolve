"""
Generate comprehensive diagrams for the Model ID System documentation.
Creates multiple figures showing:
1. Three ID types overview
2. Parts are FIXED, only colors move
3. Non-3x3 to 3x3 evolution (reduction)
4. When colors_id changes (face rotation vs cube rotation)
5. Part vs PartSlice differences
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch
import numpy as np

# Color definitions matching cube colors
COLORS = {
    'W': '#FFFFFF',  # White
    'Y': '#FFFF00',  # Yellow
    'B': '#0000FF',  # Blue
    'G': '#00FF00',  # Green
    'R': '#FF0000',  # Red
    'O': '#FFA500',  # Orange
}

FACE_COLORS = {
    'U': '#FFFFCC',  # Light yellow for Up
    'D': '#FFFFFF',  # White for Down
    'F': '#CCE5FF',  # Light blue for Front
    'B': '#CCFFCC',  # Light green for Back
    'R': '#FFCCCC',  # Light red for Right
    'L': '#FFE5CC',  # Light orange for Left
}

def draw_cube_face(ax, x, y, size, colors_grid, face_label='', title=''):
    """Draw a cube face with colored stickers."""
    n = len(colors_grid)
    cell_size = size / n

    # Draw border
    rect = patches.Rectangle((x, y), size, size, linewidth=2,
                              edgecolor='black', facecolor='none')
    ax.add_patch(rect)

    # Draw cells
    for row in range(n):
        for col in range(n):
            color = colors_grid[n-1-row][col]  # Flip row for visual
            cell = patches.Rectangle(
                (x + col * cell_size, y + row * cell_size),
                cell_size, cell_size,
                linewidth=1, edgecolor='black',
                facecolor=COLORS.get(color, '#CCCCCC')
            )
            ax.add_patch(cell)
            # Add color letter
            ax.text(x + col * cell_size + cell_size/2,
                   y + row * cell_size + cell_size/2,
                   color, ha='center', va='center', fontsize=8, fontweight='bold')

    # Face label
    if face_label:
        ax.text(x + size/2, y - 0.3, face_label, ha='center', va='top',
               fontsize=12, fontweight='bold')

    # Title above
    if title:
        ax.text(x + size/2, y + size + 0.2, title, ha='center', va='bottom',
               fontsize=10, fontweight='bold')


# ============================================================================
# DIAGRAM 1: Three ID Types Overview
# ============================================================================
def create_id_types_diagram():
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(-1, 15)
    ax.set_ylim(-1, 11)
    ax.set_aspect('equal')
    ax.axis('off')

    fig.suptitle('Three ID Types in the Cube Model', fontsize=16, fontweight='bold')

    # Title boxes for each ID type
    id_types = [
        ('fixed_id', 0, 9, '#E8F5E9', 'Based on Face NAMES\n(FaceName.F, FaceName.U)\nNEVER changes'),
        ('position_id', 5, 9, '#FFF3E0', 'Based on Face CENTER colors\nChanges on slice/cube rotation\n(M, E, S, x, y, z)'),
        ('colors_id', 10, 9, '#E3F2FD', 'Actual sticker colors\nChanges on ANY rotation\n(F, R, U, etc.)'),
    ]

    for name, x, y, color, desc in id_types:
        box = FancyBboxPatch((x, y), 4, 1.5, boxstyle="round,pad=0.05",
                             facecolor=color, edgecolor='black', linewidth=2)
        ax.add_patch(box)
        ax.text(x + 2, y + 1.1, name, ha='center', va='center',
               fontsize=12, fontweight='bold')
        ax.text(x + 2, y + 0.4, desc, ha='center', va='center',
               fontsize=8, style='italic')

    # Example cube section showing F-U edge
    ax.text(7, 7.5, 'Example: Edge at Front-Up position', ha='center',
           fontsize=11, fontweight='bold')

    # Draw simplified cube view
    # Front face
    front = [[' ', 'Y', ' '],
             ['O', 'B', 'R'],
             [' ', 'W', ' ']]
    draw_cube_face(ax, 5.5, 3.5, 3, front, 'F', '')

    # Up face (above front)
    up = [[' ', 'G', ' '],
          ['O', 'Y', 'R'],
          [' ', 'B', ' ']]
    draw_cube_face(ax, 5.5, 6.5, 3, up, 'U', '')

    # Highlight the F-U edge
    highlight = patches.Rectangle((6.5, 6.2), 1, 0.6, linewidth=3,
                                   edgecolor='red', facecolor='none', linestyle='--')
    ax.add_patch(highlight)
    ax.annotate('F-U Edge', xy=(7, 6.5), xytext=(10, 6.5),
               fontsize=10, fontweight='bold', color='red',
               arrowprops=dict(arrowstyle='->', color='red'))

    # ID values box
    id_box = FancyBboxPatch((0.5, 1), 13, 2, boxstyle="round,pad=0.1",
                            facecolor='#FAFAFA', edgecolor='gray', linewidth=1)
    ax.add_patch(id_box)

    ax.text(7, 2.7, 'For the F-U edge shown above:', ha='center', fontsize=10, fontweight='bold')
    ax.text(2, 2.0, 'fixed_id = {F, U}', ha='left', fontsize=10, family='monospace',
           bbox=dict(boxstyle='round', facecolor='#E8F5E9'))
    ax.text(5.5, 2.0, 'position_id = {BLUE, YELLOW}', ha='left', fontsize=10, family='monospace',
           bbox=dict(boxstyle='round', facecolor='#FFF3E0'))
    ax.text(10, 2.0, 'colors_id = {BLUE, YELLOW}', ha='left', fontsize=10, family='monospace',
           bbox=dict(boxstyle='round', facecolor='#E3F2FD'))
    ax.text(7, 1.3, '↑ Face names    ↑ Center colors of F & U faces    ↑ Actual sticker colors',
           ha='center', fontsize=8, color='gray')

    plt.tight_layout()
    plt.savefig('/home/user/cubesolve/design2/images/id-types-overview.png',
                dpi=150, bbox_inches='tight', facecolor='white')
    print("Created: id-types-overview.png")


# ============================================================================
# DIAGRAM 2: Parts are FIXED, Colors Move
# ============================================================================
def create_parts_fixed_diagram():
    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    fig.suptitle('Parts are FIXED in Space — Only Colors Rotate!', fontsize=16, fontweight='bold')

    # State 1: Before rotation
    ax1 = axes[0]
    ax1.set_xlim(-0.5, 4)
    ax1.set_ylim(-0.5, 4)
    ax1.set_aspect('equal')
    ax1.axis('off')
    ax1.set_title('BEFORE F rotation', fontsize=12)

    # Draw front face
    front1 = [['O', 'Y', 'R'],
              ['O', 'B', 'R'],
              ['O', 'W', 'R']]
    draw_cube_face(ax1, 0.5, 0.5, 3, front1, 'Front Face')

    # Highlight corner positions
    for pos, label in [((0.5, 3.0), 'Corner\nslot'), ((3.0, 3.0), 'Corner\nslot'),
                       ((0.5, 0.5), 'Corner\nslot'), ((3.0, 0.5), 'Corner\nslot')]:
        ax1.annotate(label, pos, fontsize=7, ha='center', va='center', color='purple')

    # Arrow to next state
    ax1.annotate('', xy=(3.8, 2), xytext=(3.5, 2),
                arrowprops=dict(arrowstyle='->', lw=2, color='green'))

    # State 2: After rotation
    ax2 = axes[1]
    ax2.set_xlim(-0.5, 4)
    ax2.set_ylim(-0.5, 4)
    ax2.set_aspect('equal')
    ax2.axis('off')
    ax2.set_title('AFTER F rotation (clockwise)', fontsize=12)

    # Front face after F rotation - colors have moved!
    front2 = [['O', 'O', 'O'],
              ['W', 'B', 'Y'],
              ['R', 'R', 'R']]
    draw_cube_face(ax2, 0.5, 0.5, 3, front2, 'Front Face')

    # Show same physical slots
    ax2.text(2, -0.3, 'Same physical slots!\nColors moved, not parts.',
            ha='center', fontsize=9, color='red', fontweight='bold')

    # State 3: Explanation
    ax3 = axes[2]
    ax3.set_xlim(-0.5, 5)
    ax3.set_ylim(-0.5, 5)
    ax3.axis('off')
    ax3.set_title('Key Insight', fontsize=12)

    explanation = """
PARTS = Physical slots in cube
        → NEVER move in 3D space
        → fixed_id stays constant

COLORS = Stickers on the cube
        → Rotate during moves
        → colors_id changes

The F-U-R corner SLOT always
exists at the same position.

Only the colored stickers
rotate through slots!
"""
    ax3.text(0, 4.5, explanation, fontsize=10, family='monospace',
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='lightyellow', edgecolor='gray'))

    # Visual representation
    ax3.add_patch(Circle((2.5, 1), 0.3, facecolor='#E8F5E9', edgecolor='black', lw=2))
    ax3.text(2.5, 1, 'Slot', ha='center', va='center', fontsize=8)
    ax3.annotate('', xy=(2.5, 0.3), xytext=(2.5, 0.7),
                arrowprops=dict(arrowstyle='->', color='blue', lw=2))
    ax3.text(2.5, 0.1, 'FIXED', ha='center', fontsize=8, fontweight='bold', color='green')

    ax3.add_patch(patches.Rectangle((3.5, 0.7), 0.6, 0.6, facecolor='red', edgecolor='black'))
    ax3.text(3.8, 1, 'R', ha='center', va='center', fontsize=10, fontweight='bold', color='white')
    ax3.annotate('', xy=(4.5, 1), xytext=(4.1, 1),
                arrowprops=dict(arrowstyle='->', color='blue', lw=2))
    ax3.text(4.7, 1, 'MOVES', ha='left', fontsize=8, fontweight='bold', color='red')

    plt.tight_layout()
    plt.savefig('/home/user/cubesolve/design2/images/parts-fixed-colors-move.png',
                dpi=150, bbox_inches='tight', facecolor='white')
    print("Created: parts-fixed-colors-move.png")


# ============================================================================
# DIAGRAM 3: Non-3x3 to 3x3 Evolution (Reduction)
# ============================================================================
def create_reduction_diagram():
    fig, axes = plt.subplots(1, 3, figsize=(16, 7))
    fig.suptitle('Evolution: Big Cube → 3x3 Reduction', fontsize=16, fontweight='bold')

    # 5x5 edge NOT reduced
    ax1 = axes[0]
    ax1.set_xlim(-0.5, 6)
    ax1.set_ylim(-1, 6)
    ax1.set_aspect('equal')
    ax1.axis('off')
    ax1.set_title('5x5 Edge: NOT Reduced\n(is3x3 = FALSE)', fontsize=11, color='red')

    # Draw edge slices with DIFFERENT colors
    edge_colors_bad = [['R', 'O', 'R', 'G', 'R'],  # Top row of edge (varied!)
                       ['B', 'G', 'B', 'O', 'B']]  # Bottom row (varied!)

    for i, color in enumerate(edge_colors_bad[0]):
        rect = patches.Rectangle((i + 0.5, 3.5), 1, 1, facecolor=COLORS[color],
                                  edgecolor='black', linewidth=2)
        ax1.add_patch(rect)
        ax1.text(i + 1, 4, f'S{i}', ha='center', va='center', fontsize=8)
    for i, color in enumerate(edge_colors_bad[1]):
        rect = patches.Rectangle((i + 0.5, 2.5), 1, 1, facecolor=COLORS[color],
                                  edgecolor='black', linewidth=2)
        ax1.add_patch(rect)

    ax1.text(3, 2, 'Each slice has DIFFERENT colors!', ha='center', fontsize=9,
            color='red', fontweight='bold')

    # Slice info
    ax1.text(0.5, 1.5, 'Slice 0: {R,B}\nSlice 1: {O,G}\nSlice 2: {R,B}\nSlice 3: {G,O}\nSlice 4: {R,B}',
            fontsize=8, family='monospace',
            bbox=dict(boxstyle='round', facecolor='#FFEBEE'))

    ax1.text(3, 0.5, '⚠️ Edge.colors_id is MEANINGLESS\n⚠️ Use slice.colors_id instead',
            ha='center', fontsize=9, color='darkred', fontweight='bold')

    # Arrow
    ax1.annotate('SOLVE\nEDGES', xy=(5.8, 3.5), xytext=(5.5, 3.5),
                fontsize=10, fontweight='bold', color='green',
                arrowprops=dict(arrowstyle='->', color='green', lw=3))

    # 5x5 edge REDUCED
    ax2 = axes[1]
    ax2.set_xlim(-0.5, 6)
    ax2.set_ylim(-1, 6)
    ax2.set_aspect('equal')
    ax2.axis('off')
    ax2.set_title('5x5 Edge: REDUCED\n(is3x3 = TRUE)', fontsize=11, color='green')

    # Draw edge slices with SAME colors
    edge_colors_good = [['R', 'R', 'R', 'R', 'R'],  # All same!
                        ['B', 'B', 'B', 'B', 'B']]

    for i, color in enumerate(edge_colors_good[0]):
        rect = patches.Rectangle((i + 0.5, 3.5), 1, 1, facecolor=COLORS[color],
                                  edgecolor='black', linewidth=2)
        ax1.add_patch(rect)
        ax2.add_patch(patches.Rectangle((i + 0.5, 3.5), 1, 1, facecolor=COLORS[color],
                                        edgecolor='black', linewidth=2))
        ax2.text(i + 1, 4, f'S{i}', ha='center', va='center', fontsize=8)
    for i, color in enumerate(edge_colors_good[1]):
        ax2.add_patch(patches.Rectangle((i + 0.5, 2.5), 1, 1, facecolor=COLORS[color],
                                        edgecolor='black', linewidth=2))

    ax2.text(3, 2, 'All slices have SAME colors!', ha='center', fontsize=9,
            color='green', fontweight='bold')

    ax2.text(0.5, 1.5, 'Slice 0: {R,B}\nSlice 1: {R,B}\nSlice 2: {R,B}\nSlice 3: {R,B}\nSlice 4: {R,B}',
            fontsize=8, family='monospace',
            bbox=dict(boxstyle='round', facecolor='#E8F5E9'))

    ax2.text(3, 0.5, '✓ Edge.colors_id = {R,B}\n✓ Now behaves like 3x3 edge!',
            ha='center', fontsize=9, color='darkgreen', fontweight='bold')

    # Summary panel
    ax3 = axes[2]
    ax3.set_xlim(-0.5, 5)
    ax3.set_ylim(-0.5, 6)
    ax3.axis('off')
    ax3.set_title('Summary: When to Use What', fontsize=11)

    summary = """
┌─────────────────────────────────┐
│  PHASE 1: Big Cube              │
│  is3x3 = FALSE                  │
├─────────────────────────────────┤
│  • Work with SLICES             │
│  • Use slice.colors_id          │
│  • Part.colors_id = undefined   │
│  • Solvers: NxNEdges, NxNCenters│
└─────────────────────────────────┘

┌─────────────────────────────────┐
│  PHASE 2: After Reduction       │
│  is3x3 = TRUE                   │
├─────────────────────────────────┤
│  • Work with PARTS              │
│  • Use part.colors_id           │
│  • Use part.in_position         │
│  • Solvers: L1Cross, OLL, PLL   │
└─────────────────────────────────┘
"""
    ax3.text(0, 5.5, summary, fontsize=9, family='monospace',
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='lightyellow'))

    plt.tight_layout()
    plt.savefig('/home/user/cubesolve/design2/images/reduction-evolution.png',
                dpi=150, bbox_inches='tight', facecolor='white')
    print("Created: reduction-evolution.png")


# ============================================================================
# DIAGRAM 4: When colors_id Changes
# ============================================================================
def create_colors_id_changes_diagram():
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('When Does colors_id Change?', fontsize=16, fontweight='bold')

    # Row 1: Face rotation (F move) - colors_id CHANGES
    ax = axes[0, 0]
    ax.set_xlim(-0.5, 4)
    ax.set_ylim(-0.5, 4)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Before F move', fontsize=10)

    face1 = [['O', 'Y', 'R'],
             ['O', 'B', 'R'],
             ['O', 'W', 'R']]
    draw_cube_face(ax, 0.5, 0.5, 3, face1, 'Front')
    ax.text(2, -0.3, 'F-U edge: {Y, B}', ha='center', fontsize=9,
           bbox=dict(boxstyle='round', facecolor='#E3F2FD'))

    ax = axes[0, 1]
    ax.set_xlim(-0.5, 4)
    ax.set_ylim(-0.5, 4)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('After F move', fontsize=10)

    face2 = [['O', 'O', 'O'],
             ['W', 'B', 'Y'],
             ['R', 'R', 'R']]
    draw_cube_face(ax, 0.5, 0.5, 3, face2, 'Front')
    ax.text(2, -0.3, 'F-U edge: {O, B}', ha='center', fontsize=9,
           bbox=dict(boxstyle='round', facecolor='#FFCDD2'))

    ax = axes[0, 2]
    ax.set_xlim(-0.5, 5)
    ax.set_ylim(-0.5, 4)
    ax.axis('off')
    ax.set_title('Face Rotation (F, R, U, etc.)', fontsize=10, color='red')

    ax.text(0, 3, '✗ colors_id CHANGES', fontsize=12, fontweight='bold', color='red')
    ax.text(0, 2.3, 'Colors rotate to new slots', fontsize=10)
    ax.text(0, 1.6, '✓ fixed_id stays same', fontsize=10, color='green')
    ax.text(0, 0.9, '✓ position_id stays same', fontsize=10, color='green')
    ax.text(0, 0.2, '(face centers don\'t move)', fontsize=9, style='italic', color='gray')

    # Row 2: Cube rotation (y move) - position_id ALSO changes!
    ax = axes[1, 0]
    ax.set_xlim(-0.5, 4)
    ax.set_ylim(-0.5, 4)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Before y rotation', fontsize=10)

    face3 = [['G', 'G', 'G'],
             ['G', 'B', 'G'],  # Blue center
             ['G', 'G', 'G']]
    draw_cube_face(ax, 0.5, 0.5, 3, face3, 'Front (Blue center)')

    ax = axes[1, 1]
    ax.set_xlim(-0.5, 4)
    ax.set_ylim(-0.5, 4)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('After y rotation', fontsize=10)

    face4 = [['B', 'B', 'B'],
             ['B', 'R', 'B'],  # Red center - was Right face!
             ['B', 'B', 'B']]
    draw_cube_face(ax, 0.5, 0.5, 3, face4, 'Front (Red center)')

    ax = axes[1, 2]
    ax.set_xlim(-0.5, 5)
    ax.set_ylim(-0.5, 4)
    ax.axis('off')
    ax.set_title('Cube/Slice Rotation (x, y, z, M, E, S)', fontsize=10, color='purple')

    ax.text(0, 3, '✗ colors_id CHANGES', fontsize=12, fontweight='bold', color='red')
    ax.text(0, 2.3, '✗ position_id CHANGES', fontsize=12, fontweight='bold', color='red')
    ax.text(0, 1.6, '(face centers rotate!)', fontsize=9, style='italic', color='gray')
    ax.text(0, 0.9, '✓ fixed_id stays same', fontsize=10, color='green')
    ax.text(0, 0.2, '(structure never changes)', fontsize=9, style='italic', color='gray')

    plt.tight_layout()
    plt.savefig('/home/user/cubesolve/design2/images/colors-id-changes.png',
                dpi=150, bbox_inches='tight', facecolor='white')
    print("Created: colors-id-changes.png")


# ============================================================================
# DIAGRAM 5: Part vs PartSlice
# ============================================================================
def create_part_vs_slice_diagram():
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(-0.5, 14)
    ax.set_ylim(-0.5, 10)
    ax.set_aspect('equal')
    ax.axis('off')

    fig.suptitle('Part vs PartSlice: The Hierarchy', fontsize=16, fontweight='bold')

    # Draw class hierarchy
    hierarchy = """
    ┌─────────────┐
    │    Cube     │
    └──────┬──────┘
           │
    ┌──────┴──────┐
    │    Face     │ (6 faces)
    └──────┬──────┘
           │
    ┌──────┴──────┐
    │    Part     │ (Edge, Corner, Center)
    └──────┬──────┘
           │
    ┌──────┴──────┐
    │  PartSlice  │ (EdgeWing, CornerSlice, CenterSlice)
    └──────┬──────┘
           │
    ┌──────┴──────┐
    │  PartEdge   │ (individual sticker)
    └─────────────┘
    """

    # Draw boxes for hierarchy
    boxes = [
        (5, 9, 'Cube', '#B3E5FC'),
        (5, 7.5, 'Face (×6)', '#C8E6C9'),
        (5, 6, 'Part\n(Edge, Corner, Center)', '#FFF9C4'),
        (5, 4, 'PartSlice\n(EdgeWing, CornerSlice)', '#FFCCBC'),
        (5, 2, 'PartEdge\n(sticker)', '#E1BEE7'),
    ]

    for x, y, label, color in boxes:
        box = FancyBboxPatch((x, y), 4, 1.2, boxstyle="round,pad=0.05",
                             facecolor=color, edgecolor='black', linewidth=2)
        ax.add_patch(box)
        ax.text(x + 2, y + 0.6, label, ha='center', va='center', fontsize=10, fontweight='bold')

    # Draw connecting lines
    for y in [8.7, 7.2, 5.7, 3.7]:
        ax.plot([7, 7], [y, y - 0.3], 'k-', lw=2)

    # Right side: 5x5 edge visualization
    ax.text(11.5, 9.5, '5×5 Edge Example', fontsize=12, fontweight='bold', ha='center')

    # Draw the 5x5 edge
    edge_top = ['R', 'R', 'R', 'R', 'R']
    edge_bot = ['B', 'B', 'B', 'B', 'B']

    for i in range(5):
        # Top row
        rect = patches.Rectangle((9.5 + i * 0.8, 8), 0.8, 0.8,
                                  facecolor=COLORS[edge_top[i]], edgecolor='black', lw=2)
        ax.add_patch(rect)
        # Bottom row
        rect = patches.Rectangle((9.5 + i * 0.8, 7.2), 0.8, 0.8,
                                  facecolor=COLORS[edge_bot[i]], edgecolor='black', lw=2)
        ax.add_patch(rect)

    # Labels
    ax.text(11.5, 6.8, 'Edge (Part) - contains 5 slices', ha='center', fontsize=9)

    # Show one slice
    ax.annotate('', xy=(10.3, 6.5), xytext=(10.3, 7.2),
               arrowprops=dict(arrowstyle='->', color='red', lw=2))

    ax.add_patch(patches.Rectangle((9.8, 5.5), 0.8, 0.8, facecolor=COLORS['R'],
                                   edgecolor='red', lw=3))
    ax.add_patch(patches.Rectangle((9.8, 4.7), 0.8, 0.8, facecolor=COLORS['B'],
                                   edgecolor='red', lw=3))
    ax.text(11.5, 5.2, 'EdgeWing (PartSlice)\nSlice 0: {R, B}', ha='left', fontsize=9)

    # Show one PartEdge
    ax.annotate('', xy=(10.2, 4.2), xytext=(10.2, 4.7),
               arrowprops=dict(arrowstyle='->', color='purple', lw=2))

    ax.add_patch(patches.Rectangle((9.8, 3.4), 0.8, 0.8, facecolor=COLORS['R'],
                                   edgecolor='purple', lw=3))
    ax.text(11.5, 3.8, 'PartEdge (sticker)\ncolor = RED', ha='left', fontsize=9)

    # Comparison table
    table_y = 1.5
    ax.text(7, table_y + 0.8, 'ID Availability:', fontsize=11, fontweight='bold', ha='center')

    table = """
┌─────────────┬────────────┬─────────────┬───────────┐
│             │  fixed_id  │ position_id │ colors_id │
├─────────────┼────────────┼─────────────┼───────────┤
│ Part        │     ✓      │   ✓ (3x3)   │  ✓ (3x3)  │
│ PartSlice   │     ✓      │      ✗      │     ✓     │
│ PartEdge    │     ✗      │      ✗      │  (color)  │
└─────────────┴────────────┴─────────────┴───────────┘
"""
    ax.text(7, table_y - 0.8, table, fontsize=9, family='monospace', ha='center', va='top',
           bbox=dict(boxstyle='round', facecolor='#FAFAFA'))

    plt.tight_layout()
    plt.savefig('/home/user/cubesolve/design2/images/part-vs-slice.png',
                dpi=150, bbox_inches='tight', facecolor='white')
    print("Created: part-vs-slice.png")


# ============================================================================
# Run all
# ============================================================================
if __name__ == '__main__':
    create_id_types_diagram()
    create_parts_fixed_diagram()
    create_reduction_diagram()
    create_colors_id_changes_diagram()
    create_part_vs_slice_diagram()
    print("\nAll diagrams created successfully!")
