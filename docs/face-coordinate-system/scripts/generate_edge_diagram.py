"""
Generate a clean diagram of the edge coordinate system.
Shows R/T directions for all 12 edges and whether they match (same_direction).
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch
import numpy as np

# Create figure with white background
fig, axes = plt.subplots(1, 2, figsize=(16, 10))
fig.suptitle('Edge Coordinate System: right_top_left_same_direction', fontsize=16, fontweight='bold')

# ===== LEFT PANEL: 3D Isometric View =====
ax1 = axes[0]
ax1.set_xlim(-0.5, 4.5)
ax1.set_ylim(-0.5, 4.5)
ax1.set_aspect('equal')
ax1.axis('off')
ax1.set_title('3D View - All 12 Edges', fontsize=12, fontweight='bold')

# Isometric cube vertices (approximate)
# Front face: bottom-left, bottom-right, top-right, top-left
front = [(0.5, 0.5), (2.5, 0.5), (2.5, 2.5), (0.5, 2.5)]
# Back face (shifted up-right for isometric)
back = [(1.5, 1.5), (3.5, 1.5), (3.5, 3.5), (1.5, 3.5)]

# Draw cube edges
cube_color = '#333333'
lw = 2

# Front face
for i in range(4):
    ax1.plot([front[i][0], front[(i+1)%4][0]],
             [front[i][1], front[(i+1)%4][1]], color=cube_color, lw=lw)
# Back face
for i in range(4):
    ax1.plot([back[i][0], back[(i+1)%4][0]],
             [back[i][1], back[(i+1)%4][1]], color=cube_color, lw=lw)
# Connecting edges
for i in range(4):
    ax1.plot([front[i][0], back[i][0]],
             [front[i][1], back[i][1]], color=cube_color, lw=lw)

# Face labels
ax1.text(1.5, 1.5, 'F', fontsize=14, ha='center', va='center', color='blue', fontweight='bold')
ax1.text(2.5, 2.5, 'U', fontsize=14, ha='center', va='center', color='blue', fontweight='bold')
ax1.text(3.2, 2.0, 'R', fontsize=14, ha='center', va='center', color='blue', fontweight='bold')
ax1.text(0.3, 2.0, 'L', fontsize=14, ha='center', va='center', color='blue', fontweight='bold')
ax1.text(1.5, 0.2, 'D', fontsize=14, ha='center', va='center', color='blue', fontweight='bold')
ax1.text(2.8, 3.2, 'B', fontsize=14, ha='center', va='center', color='blue', fontweight='bold')

# Edge annotations with same_direction status
# Format: (midpoint, label, is_same_direction)
edge_labels = [
    # Front face edges (all TRUE)
    ((1.5, 2.5), 'F-U', True),
    ((0.5, 1.5), 'F-L', True),
    ((2.5, 1.5), 'F-R', True),
    ((1.5, 0.5), 'F-D', True),
    # Back face edges
    ((2.5, 3.5), 'U-B', False),
    ((3.5, 2.5), 'R-B', True),
    ((1.5, 3.5), 'L-B', True),
    ((2.5, 1.5), 'D-B', False),
    # Vertical connecting edges
    ((1.0, 3.0), 'L-U', False),
    ((3.0, 3.0), 'U-R', True),
    ((1.0, 1.0), 'L-D', True),
    ((3.0, 1.0), 'D-R', False),
]

# Add edge status indicators
for pos, label, is_same in edge_labels:
    color = '#228B22' if is_same else '#DC143C'  # Green for True, Red for False
    symbol = '✓' if is_same else '✗'
    ax1.annotate(f'{symbol}', pos, fontsize=10, ha='center', va='center',
                color=color, fontweight='bold',
                bbox=dict(boxstyle='circle,pad=0.1', facecolor='white', edgecolor=color, lw=1.5))

# Legend for left panel
ax1.text(0.5, -0.2, '✓ = same_direction (True)', fontsize=10, color='#228B22', fontweight='bold')
ax1.text(2.5, -0.2, '✗ = opposite (False)', fontsize=10, color='#DC143C', fontweight='bold')

# ===== RIGHT PANEL: Unfolded Cube View =====
ax2 = axes[1]
ax2.set_xlim(-0.5, 12.5)
ax2.set_ylim(-0.5, 9.5)
ax2.set_aspect('equal')
ax2.axis('off')
ax2.set_title('Unfolded View - R/T Directions per Face', fontsize=12, fontweight='bold')

# Draw unfolded cube (cross pattern)
# Each face is 3x3 units
face_positions = {
    'U': (3, 6),  # top
    'L': (0, 3),  # left
    'F': (3, 3),  # center
    'R': (6, 3),  # right
    'B': (9, 3),  # far right
    'D': (3, 0),  # bottom
}

face_colors = {
    'U': '#FFFFCC',  # light yellow
    'L': '#FFCCCC',  # light red/orange
    'F': '#CCFFCC',  # light green
    'R': '#CCE5FF',  # light blue
    'B': '#E5CCFF',  # light purple
    'D': '#FFFFFF',  # white
}

def draw_face(ax, x, y, label, color):
    """Draw a face with R and T direction arrows and ltr numbering on edges."""
    # Face rectangle
    rect = patches.Rectangle((x, y), 3, 3, linewidth=2,
                              edgecolor='black', facecolor=color)
    ax.add_patch(rect)

    # Face label
    ax.text(x + 1.5, y + 1.5, label, fontsize=16, ha='center', va='center',
            fontweight='bold', color='#333333')

    # R arrow (right direction) - blue
    ax.annotate('', xy=(x + 2.8, y + 1.5), xytext=(x + 0.2, y + 1.5),
                arrowprops=dict(arrowstyle='->', color='blue', lw=2))
    ax.text(x + 2.9, y + 1.5, 'R', fontsize=10, color='blue', fontweight='bold', va='center')

    # T arrow (top direction) - red
    ax.annotate('', xy=(x + 1.5, y + 2.8), xytext=(x + 1.5, y + 0.2),
                arrowprops=dict(arrowstyle='->', color='red', lw=2))
    ax.text(x + 1.5, y + 2.9, 'T', fontsize=10, color='red', fontweight='bold', ha='center')

    # LTR numbering on each edge (0→1→2)
    # Dark green for ltr labels
    ltr_color = '#006400'

    # Bottom edge (horizontal): ltr 0→1→2 from left to right
    for i in range(3):
        ax.text(x + 0.5 + i, y - 0.15, str(i), fontsize=8, ha='center', va='top',
                color=ltr_color, fontweight='bold')

    # Top edge (horizontal): ltr 0→1→2 from left to right
    for i in range(3):
        ax.text(x + 0.5 + i, y + 3.15, str(i), fontsize=8, ha='center', va='bottom',
                color=ltr_color, fontweight='bold')

    # Left edge (vertical): ltr 0→1→2 from bottom to top
    for i in range(3):
        ax.text(x - 0.15, y + 0.5 + i, str(i), fontsize=8, ha='right', va='center',
                color=ltr_color, fontweight='bold')

    # Right edge (vertical): ltr 0→1→2 from bottom to top
    for i in range(3):
        ax.text(x + 3.15, y + 0.5 + i, str(i), fontsize=8, ha='left', va='center',
                color=ltr_color, fontweight='bold')

# Draw all faces
for face, (x, y) in face_positions.items():
    draw_face(ax2, x, y, face, face_colors[face])

# Add edge relationship annotations between faces
edge_annotations = [
    # (x, y, text, color) - positioned between faces
    (4.5, 5.7, 'F-U: ✓ SAME', '#228B22'),
    (4.5, 3.3, 'F-D: ✓ SAME', '#228B22'),
    (2.7, 4.5, 'F-L: ✓ SAME', '#228B22'),
    (6.3, 4.5, 'F-R: ✓ SAME', '#228B22'),
    (2.7, 7.5, 'L-U: ✗ OPP', '#DC143C'),
    (6.3, 7.5, 'U-R: ✓ SAME', '#228B22'),
    (2.7, 1.5, 'L-D: ✓ SAME', '#228B22'),
    (6.3, 1.5, 'D-R: ✗ OPP', '#DC143C'),
    (9.3, 7.5, 'U-B: ✗ OPP', '#DC143C'),
    (9.3, 4.5, 'R-B: ✓ SAME', '#228B22'),
    (9.3, 1.5, 'D-B: ✗ OPP', '#DC143C'),
    (12.3, 4.5, 'L-B: ✓ SAME', '#228B22'),
]

for x, y, text, color in edge_annotations:
    ax2.text(x, y, text, fontsize=8, color=color, fontweight='bold',
             rotation=90 if 'L-U' in text or 'U-R' in text or 'L-D' in text or 'D-R' in text or 'U-B' in text or 'D-B' in text else 0,
             ha='center', va='center')

# Summary box
summary_text = """SUMMARY:
8 edges: same_direction = True (✓)
4 edges: same_direction = False (✗)

FALSE edges: L-U, U-B, D-R, D-B
(All involve L or B with U or D)"""

ax2.text(0.5, 8.5, summary_text, fontsize=9,
         bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', edgecolor='gray'),
         verticalalignment='top', family='monospace')

plt.tight_layout()
plt.savefig('/home/user/cubesolve/coor-system-doc/edge-coordinate-system.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.savefig('/home/user/cubesolve/docs/design2/images/edge-coordinate-system.png',
            dpi=150, bbox_inches='tight', facecolor='white')
print("Diagram saved!")
