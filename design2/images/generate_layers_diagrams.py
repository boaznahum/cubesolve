"""
Generate diagrams for the Layers and Dependencies documentation.
Creates:
1. Package hierarchy diagram
2. First-level dependencies with WRONG direction (RED) markers
3. Second-level dependencies with WRONG direction (RED) markers
4. Combined layers diagram

Violations (as of 2025-12-07):
- V1: FIXED - domain.exceptions created, no longer imports from application.exceptions
- V2: FIXED - domain.solver.protocols created, domain imports protocols not concrete classes
- V3: domain.model imports from presentation.viewer (2 files) - OPEN
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

# Color scheme for layers
LAYER_COLORS = {
    'application': '#ADD8E6',   # Light Blue
    'domain': '#90EE90',        # Light Green
    'presentation': '#FFFFE0',  # Light Yellow
    'utils': '#D3D3D3',         # Light Gray
    'resources': '#E6E6FA',     # Lavender
}

SUBLAYER_COLORS = {
    'application': '#E6F3FF',
    'domain': '#E8F5E9',
    'presentation': '#FFFDE7',
    'utils': '#F5F5F5',
    'resources': '#F3E5F5',
}


def create_layers_hierarchy_diagram():
    """Create package hierarchy diagram."""
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(-1, 17)
    ax.set_ylim(-1, 13)
    ax.set_aspect('equal')
    ax.axis('off')

    fig.suptitle('Package Hierarchy - src/cube/', fontsize=18, fontweight='bold', y=0.95)

    # Main container
    main_box = FancyBboxPatch((-0.5, 0), 17, 12, boxstyle="round,pad=0.1",
                               facecolor='#FAFAFA', edgecolor='black', linewidth=2)
    ax.add_patch(main_box)
    ax.text(8.25, 11.5, 'src/cube/', ha='center', va='center', fontsize=14, fontweight='bold')

    # Application layer
    app_box = FancyBboxPatch((0, 8), 5, 3, boxstyle="round,pad=0.05",
                              facecolor=LAYER_COLORS['application'], edgecolor='black', linewidth=2)
    ax.add_patch(app_box)
    ax.text(2.5, 10.5, 'application/', ha='center', va='center', fontsize=12, fontweight='bold')

    # Application sublayers
    for i, (name, desc) in enumerate([('animation', 'Animation mgmt'),
                                       ('commands', 'Operator system'),
                                       ('exceptions', 'Custom exceptions')]):
        box = FancyBboxPatch((0.2 + i*1.6, 8.2), 1.4, 1.8, boxstyle="round,pad=0.03",
                              facecolor=SUBLAYER_COLORS['application'], edgecolor='gray', linewidth=1)
        ax.add_patch(box)
        ax.text(0.9 + i*1.6, 9.4, name, ha='center', va='center', fontsize=7, fontweight='bold')
        ax.text(0.9 + i*1.6, 8.8, desc, ha='center', va='center', fontsize=5, style='italic')

    # Domain layer
    dom_box = FancyBboxPatch((5.5, 4), 5.5, 7, boxstyle="round,pad=0.05",
                              facecolor=LAYER_COLORS['domain'], edgecolor='black', linewidth=2)
    ax.add_patch(dom_box)
    ax.text(8.25, 10.5, 'domain/', ha='center', va='center', fontsize=12, fontweight='bold')

    # Domain sublayers
    domain_subs = [
        ('algs', 'Algorithms', 5.7, 8.5, 1.6, 1.5),
        ('model', 'Cube model', 7.5, 8.5, 1.6, 1.5),
        ('solver', 'Solvers', 9.3, 8.5, 1.5, 1.5),
    ]
    for name, desc, x, y, w, h in domain_subs:
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03",
                              facecolor=SUBLAYER_COLORS['domain'], edgecolor='gray', linewidth=1)
        ax.add_patch(box)
        ax.text(x + w/2, y + h - 0.3, name, ha='center', va='center', fontsize=8, fontweight='bold')
        ax.text(x + w/2, y + h - 0.7, desc, ha='center', va='center', fontsize=6, style='italic')

    # Solver sublayers
    solver_subs = [('beginner', 5.9, 4.3), ('CFOP', 7.5, 4.3), ('common', 9.1, 4.3)]
    for name, x, y in solver_subs:
        box = FancyBboxPatch((x, y), 1.4, 0.8, boxstyle="round,pad=0.02",
                              facecolor='#C8E6C9', edgecolor='gray', linewidth=1)
        ax.add_patch(box)
        ax.text(x + 0.7, y + 0.4, name, ha='center', va='center', fontsize=6)

    # Arrow from solver to sub-solvers
    ax.annotate('', xy=(8, 5.1), xytext=(8, 8.5),
                arrowprops=dict(arrowstyle='->', color='gray', lw=1))

    # Presentation layer
    pres_box = FancyBboxPatch((11.5, 2), 5, 9, boxstyle="round,pad=0.05",
                               facecolor=LAYER_COLORS['presentation'], edgecolor='black', linewidth=2)
    ax.add_patch(pres_box)
    ax.text(14, 10.5, 'presentation/', ha='center', va='center', fontsize=12, fontweight='bold')

    # GUI box
    gui_box = FancyBboxPatch((11.7, 3), 4.6, 6.5, boxstyle="round,pad=0.03",
                              facecolor=SUBLAYER_COLORS['presentation'], edgecolor='gray', linewidth=1)
    ax.add_patch(gui_box)
    ax.text(14, 9.2, 'gui/', ha='center', va='center', fontsize=10, fontweight='bold')

    # GUI sublayers
    gui_subs = [
        ('backends/', 11.9, 5.5, 4.2, 3.2),
        ('commands/', 11.9, 3.2, 1.3, 1.0),
        ('effects/', 13.4, 3.2, 1.2, 1.0),
        ('protocols/', 14.8, 3.2, 1.3, 1.0),
    ]
    for name, x, y, w, h in gui_subs:
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                              facecolor='#FFF9C4', edgecolor='gray', linewidth=1)
        ax.add_patch(box)
        ax.text(x + w/2, y + h/2, name, ha='center', va='center', fontsize=7, fontweight='bold')

    # Backends list
    backends = ['console', 'headless', 'pyglet', 'pyglet2', 'tkinter', 'web']
    for i, name in enumerate(backends):
        x = 12.1 + (i % 3) * 1.3
        y = 7.5 - (i // 3) * 0.8
        ax.text(x, y, f'[{name}]', ha='left', va='center', fontsize=6)

    # Viewer
    viewer_box = FancyBboxPatch((11.9, 2.2), 2, 0.6, boxstyle="round,pad=0.02",
                                 facecolor=SUBLAYER_COLORS['presentation'], edgecolor='gray', linewidth=1)
    ax.add_patch(viewer_box)
    ax.text(12.9, 2.5, 'viewer/', ha='center', va='center', fontsize=8, fontweight='bold')

    # Utils layer
    utils_box = FancyBboxPatch((0, 4), 2, 1.5, boxstyle="round,pad=0.05",
                                facecolor=LAYER_COLORS['utils'], edgecolor='black', linewidth=2)
    ax.add_patch(utils_box)
    ax.text(1, 4.75, 'utils/', ha='center', va='center', fontsize=10, fontweight='bold')

    # Resources layer
    res_box = FancyBboxPatch((0, 0.5), 2.5, 2.5, boxstyle="round,pad=0.05",
                              facecolor=LAYER_COLORS['resources'], edgecolor='black', linewidth=2)
    ax.add_patch(res_box)
    ax.text(1.25, 2.5, 'resources/', ha='center', va='center', fontsize=10, fontweight='bold')

    # Resources sublayer
    faces_box = FancyBboxPatch((0.2, 0.7), 2, 1, boxstyle="round,pad=0.02",
                                facecolor='#E1BEE7', edgecolor='gray', linewidth=1)
    ax.add_patch(faces_box)
    ax.text(1.2, 1.2, 'faces/', ha='center', va='center', fontsize=8, fontweight='bold')

    plt.tight_layout()
    plt.savefig('layers-hierarchy.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("Created: layers-hierarchy.png")


def create_dependencies_first_level_diagram():
    """Create first-level dependencies diagram with RED wrong-direction arrows."""
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(-1, 15)
    ax.set_ylim(-1, 11)
    ax.set_aspect('equal')
    ax.axis('off')

    fig.suptitle('First Level Package Dependencies', fontsize=18, fontweight='bold', y=0.95)

    # Package positions (circular layout)
    packages = {
        'application': (3, 8, LAYER_COLORS['application']),
        'domain': (7, 5, LAYER_COLORS['domain']),
        'presentation': (11, 8, LAYER_COLORS['presentation']),
        'utils': (3, 2, LAYER_COLORS['utils']),
        'resources': (11, 2, LAYER_COLORS['resources']),
    }

    # Draw packages
    for name, (x, y, color) in packages.items():
        box = FancyBboxPatch((x-1.5, y-0.75), 3, 1.5, boxstyle="round,pad=0.1",
                              facecolor=color, edgecolor='black', linewidth=2)
        ax.add_patch(box)
        ax.text(x, y, name, ha='center', va='center', fontsize=12, fontweight='bold')

    # Helper to draw arrows
    def draw_arrow(start, end, color='gray', style='->', offset=0):
        x1, y1 = packages[start][:2]
        x2, y2 = packages[end][:2]
        dx, dy = x2 - x1, y2 - y1
        length = (dx**2 + dy**2)**0.5
        nx, ny = -dy/length, dx/length
        arrow = FancyArrowPatch((x1 + nx*offset, y1 + ny*offset),
                                 (x2 + nx*offset, y2 + ny*offset),
                                 arrowstyle=style, color=color,
                                 mutation_scale=15, lw=2,
                                 connectionstyle="arc3,rad=0.1")
        ax.add_patch(arrow)

    # Correct direction dependencies (gray) - top to bottom
    draw_arrow('application', 'domain', color='gray', offset=0.2)
    draw_arrow('presentation', 'domain', color='gray', offset=-0.2)
    draw_arrow('presentation', 'application', color='gray', offset=0.2)
    draw_arrow('domain', 'utils', color='gray')
    draw_arrow('presentation', 'resources', color='gray')

    # WRONG direction dependencies (RED) - bottom to top
    # V2 FIXED - domain now uses protocols, no direct import from application.commands
    draw_arrow('domain', 'presentation', color='red', offset=0.2)  # V3: viewer (OPEN)

    # Legend
    legend_y = 0.5
    ax.add_patch(FancyBboxPatch((3.5, legend_y-0.3), 7, 1.2, boxstyle="round,pad=0.1",
                                 facecolor='#FAFAFA', edgecolor='black', linewidth=1))
    ax.text(7, legend_y + 0.6, 'Legend:', ha='center', va='center', fontsize=10, fontweight='bold')

    ax.annotate('', xy=(5, legend_y), xytext=(4, legend_y),
                arrowprops=dict(arrowstyle='->', color='gray', lw=2))
    ax.text(5.3, legend_y, 'Correct (top→bottom)', ha='left', va='center', fontsize=9)

    ax.annotate('', xy=(8.5, legend_y), xytext=(7.5, legend_y),
                arrowprops=dict(arrowstyle='->', color='red', lw=2))
    ax.text(8.8, legend_y, 'WRONG (V3 only)', ha='left', va='center',
            fontsize=9, color='red', fontweight='bold')

    plt.tight_layout()
    plt.savefig('dependencies-first-level.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("Created: dependencies-first-level.png")


def create_dependencies_second_level_diagram():
    """Create second-level dependencies diagram."""
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(-1, 17)
    ax.set_ylim(-1, 13)
    ax.set_aspect('equal')
    ax.axis('off')

    fig.suptitle('Second Level Package Dependencies', fontsize=18, fontweight='bold', y=0.95)

    # Sublayer positions
    sublayers = {
        # Application
        'app.animation': (1, 10, '#ADD8E6'),
        'app.commands': (3.5, 10, '#ADD8E6'),
        'app.exceptions': (1, 8, '#ADD8E6'),
        'app.state': (3.5, 8, '#ADD8E6'),
        # Domain
        'dom.model': (7, 10, '#90EE90'),
        'dom.algs': (9.5, 10, '#90EE90'),
        'dom.solver': (8.25, 8, '#90EE90'),
        # Presentation
        'pres.gui': (13, 10, '#FFFFE0'),
        'pres.viewer': (15, 8, '#FFFFE0'),
        # Utils
        'utils': (4, 5, '#D3D3D3'),
        # Resources
        'resources': (12, 5, '#E6E6FA'),
    }

    # Draw sublayers
    for name, (x, y, color) in sublayers.items():
        short_name = name.split('.')[-1] if '.' in name else name
        box = FancyBboxPatch((x-0.9, y-0.5), 1.8, 1, boxstyle="round,pad=0.05",
                              facecolor=color, edgecolor='black', linewidth=1.5)
        ax.add_patch(box)
        ax.text(x, y, short_name, ha='center', va='center', fontsize=9, fontweight='bold')

    # Layer labels
    ax.text(2.25, 11.5, 'APPLICATION', ha='center', va='center', fontsize=11,
            fontweight='bold', color='#1565C0')
    ax.text(8.25, 11.5, 'DOMAIN', ha='center', va='center', fontsize=11,
            fontweight='bold', color='#2E7D32')
    ax.text(14, 11.5, 'PRESENTATION', ha='center', va='center', fontsize=11,
            fontweight='bold', color='#F57F17')

    # Normal dependencies (gray arrows)
    normal_deps = [
        ('dom.solver', 'dom.model'),
        ('dom.solver', 'dom.algs'),
        ('dom.algs', 'dom.model'),
        ('app.animation', 'dom.model'),
        ('app.commands', 'dom.algs'),
        ('app.state', 'dom.model'),
        ('pres.gui', 'dom.model'),
        ('pres.gui', 'app.state'),
        ('pres.gui', 'app.animation'),
        ('pres.viewer', 'dom.model'),
        ('dom.model', 'utils'),
    ]

    for start, end in normal_deps:
        x1, y1 = sublayers[start][:2]
        x2, y2 = sublayers[end][:2]
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color='gray', lw=1.5,
                                    connectionstyle="arc3,rad=0.1"))

    # RED dependencies - WRONG direction (domain -> application/presentation)
    # V1 (exceptions) FIXED - domain now has its own exceptions
    # V2 FIXED - domain now uses protocols, no direct import from application.commands
    # V3: domain.model imports from presentation.viewer (2 files) - OPEN
    red_deps = [
        ('dom.model', 'pres.viewer', 'V3: domain→pres'),
    ]

    for start, end, label in red_deps:
        x1, y1 = sublayers[start][:2]
        x2, y2 = sublayers[end][:2]
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color='red', lw=2.5,
                                    connectionstyle="arc3,rad=0.15"))
        # Label
        mx, my = (x1+x2)/2, (y1+y2)/2 + 0.4
        ax.text(mx, my, label, ha='center', va='center', fontsize=7,
                color='red', fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # Legend
    ax.add_patch(FancyBboxPatch((5, 1.5), 6, 2.5, boxstyle="round,pad=0.1",
                                 facecolor='#FAFAFA', edgecolor='black', linewidth=1))
    ax.text(8, 3.5, 'Legend:', ha='center', va='center', fontsize=10, fontweight='bold')

    ax.annotate('', xy=(6.5, 2.8), xytext=(5.5, 2.8),
                arrowprops=dict(arrowstyle='->', color='gray', lw=1.5))
    ax.text(7, 2.8, 'Normal dependency', ha='left', va='center', fontsize=9)

    ax.annotate('', xy=(6.5, 2.1), xytext=(5.5, 2.1),
                arrowprops=dict(arrowstyle='->', color='red', lw=2.5))
    ax.text(7, 2.1, 'WRONG direction (V3 only)', ha='left', va='center',
            fontsize=9, color='red', fontweight='bold')

    plt.tight_layout()
    plt.savefig('dependencies-second-level.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("Created: dependencies-second-level.png")


def create_combined_layers_diagram():
    """Create single comprehensive diagram: hierarchy + all dependencies."""
    fig, ax = plt.subplots(1, 1, figsize=(20, 16))
    ax.set_xlim(-1, 21)
    ax.set_ylim(-1, 17)
    ax.set_aspect('equal')
    ax.axis('off')

    fig.suptitle('Package Layers and Dependencies - src/cube/', fontsize=18, fontweight='bold', y=0.97)

    # Layer positions (bottom to top: utils/resources, domain, application, presentation)
    # Each layer is a colored rectangle containing its second-level packages

    # === UTILS (bottom left) ===
    utils_box = FancyBboxPatch((0, 0), 3, 2.5, boxstyle="round,pad=0.1",
                                facecolor=LAYER_COLORS['utils'], edgecolor='black', linewidth=2)
    ax.add_patch(utils_box)
    ax.text(1.5, 2.1, 'utils', ha='center', va='center', fontsize=11, fontweight='bold')

    # === RESOURCES (bottom right) ===
    res_box = FancyBboxPatch((15, 0), 3, 2.5, boxstyle="round,pad=0.1",
                              facecolor=LAYER_COLORS['resources'], edgecolor='black', linewidth=2)
    ax.add_patch(res_box)
    ax.text(16.5, 2.1, 'resources', ha='center', va='center', fontsize=11, fontweight='bold')
    # faces sublayer
    ax.add_patch(FancyBboxPatch((15.3, 0.3), 2.4, 1.2, boxstyle="round,pad=0.03",
                                 facecolor=SUBLAYER_COLORS['resources'], edgecolor='gray'))
    ax.text(16.5, 0.9, 'faces/', ha='center', va='center', fontsize=9)

    # === DOMAIN (middle) ===
    dom_box = FancyBboxPatch((4, 0), 10, 5, boxstyle="round,pad=0.1",
                              facecolor=LAYER_COLORS['domain'], edgecolor='black', linewidth=2)
    ax.add_patch(dom_box)
    ax.text(9, 4.5, 'domain', ha='center', va='center', fontsize=12, fontweight='bold')

    # Domain sublayers
    dom_subs = [
        ('model', 4.3, 2.8, 2.8, 1.3),
        ('algs', 7.3, 2.8, 2.4, 1.3),
        ('solver', 10, 2.8, 3.7, 1.3),
        ('exceptions', 4.3, 0.3, 2.5, 1.2),
    ]
    for name, x, y, w, h in dom_subs:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03",
                                     facecolor=SUBLAYER_COLORS['domain'], edgecolor='gray'))
        ax.text(x + w/2, y + h/2, name, ha='center', va='center', fontsize=9, fontweight='bold')

    # Solver sub-sublayers with boxes (including protocols for V2 fix)
    solver_subs = [('beginner', 10.2, 1.5, 1.1, 0.6), ('CFOP', 11.4, 1.5, 0.9, 0.6), ('common', 12.4, 1.5, 1.1, 0.6),
                   ('protocols', 10.2, 0.4, 1.4, 0.6)]  # V2 fix location
    for name, x, y, w, h in solver_subs:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                                     facecolor='#C8E6C9', edgecolor='gray'))
        ax.text(x + w/2, y + h/2, name, ha='center', va='center', fontsize=6)

    # === APPLICATION (upper left) ===
    app_box = FancyBboxPatch((0, 6), 7, 4, boxstyle="round,pad=0.1",
                              facecolor=LAYER_COLORS['application'], edgecolor='black', linewidth=2)
    ax.add_patch(app_box)
    ax.text(3.5, 9.5, 'application', ha='center', va='center', fontsize=12, fontweight='bold')

    # Application sublayers
    app_subs = [
        ('animation', 0.3, 7.5, 2, 1.2),
        ('commands', 2.5, 7.5, 2.2, 1.2),
        ('exceptions', 4.9, 7.5, 1.8, 1.2),
        ('state', 0.3, 6.2, 2, 1),
    ]
    for name, x, y, w, h in app_subs:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03",
                                     facecolor=SUBLAYER_COLORS['application'], edgecolor='gray'))
        ax.text(x + w/2, y + h/2, name, ha='center', va='center', fontsize=8, fontweight='bold')

    # === PRESENTATION (upper right) ===
    pres_box = FancyBboxPatch((8, 6), 10, 7, boxstyle="round,pad=0.1",
                               facecolor=LAYER_COLORS['presentation'], edgecolor='black', linewidth=2)
    ax.add_patch(pres_box)
    ax.text(13, 12.5, 'presentation', ha='center', va='center', fontsize=12, fontweight='bold')

    # Presentation sublayers
    pres_subs = [
        ('gui/', 8.3, 7.5, 6, 4.5),
        ('viewer/', 14.5, 7.5, 3.2, 2),
    ]
    for name, x, y, w, h in pres_subs:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03",
                                     facecolor=SUBLAYER_COLORS['presentation'], edgecolor='gray'))
        ax.text(x + w/2, y + h - 0.4, name, ha='center', va='center', fontsize=9, fontweight='bold')

    # GUI sub-sublayers with backends list
    gui_sub_boxes = [
        ('backends/', 8.5, 8.5, 3.5, 2.5),
        ('commands/', 12.2, 8.5, 1.5, 0.8),
        ('effects/', 12.2, 7.6, 1.5, 0.8),
        ('protocols/', 8.5, 7.6, 1.5, 0.8),
    ]
    for name, x, y, w, h in gui_sub_boxes:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                                     facecolor='#FFF9C4', edgecolor='gray'))
        ax.text(x + w/2, y + h - 0.25, name, ha='center', va='center', fontsize=7, fontweight='bold')

    # Backends list inside backends box
    backends = ['console', 'headless', 'pyglet', 'pyglet2', 'tkinter', 'web']
    for i, name in enumerate(backends):
        x = 8.7 + (i % 3) * 1.1
        y = 10.2 - (i // 3) * 0.5
        ax.text(x, y, f'[{name}]', ha='left', va='center', fontsize=5)

    # === ARROWS ===
    # Helper for arrows
    def arrow(x1, y1, x2, y2, color, label=None):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color=color, lw=2,
                                    connectionstyle="arc3,rad=0.1"))
        if label:
            mx, my = (x1+x2)/2, (y1+y2)/2
            ax.text(mx, my + 0.3, label, ha='center', va='center', fontsize=7,
                    color=color, fontweight='bold',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # CORRECT (gray/green) arrows - top to bottom
    arrow(3.5, 6, 5, 5, 'green')       # app.commands -> domain.model
    arrow(13, 7.5, 9, 5, 'green')      # pres.gui -> domain
    arrow(16, 7.5, 9, 5, 'green')      # pres.viewer -> domain.model
    arrow(4.3, 6, 1.5, 2.5, 'green')   # app -> utils
    arrow(15, 6, 16.5, 2.5, 'green')   # pres -> resources

    # WRONG DIRECTION (red) arrows - bottom to top
    # V2 FIXED - domain now uses protocols, no direct import from application.commands
    arrow(6, 4, 15.5, 7.5, 'red', 'V3')   # domain.model -> pres.viewer (OPEN)

    # Legend
    ax.add_patch(FancyBboxPatch((0, 11), 6.5, 2.5, boxstyle="round,pad=0.1",
                                 facecolor='#FAFAFA', edgecolor='black', linewidth=1))
    ax.text(3.25, 13, 'Legend:', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.annotate('', xy=(2, 12.2), xytext=(1, 12.2),
                arrowprops=dict(arrowstyle='->', color='green', lw=2))
    ax.text(2.3, 12.2, 'Correct (top→bottom)', ha='left', va='center', fontsize=9)
    ax.annotate('', xy=(2, 11.4), xytext=(1, 11.4),
                arrowprops=dict(arrowstyle='->', color='red', lw=2))
    ax.text(2.3, 11.4, 'WRONG direction', ha='left', va='center', fontsize=9, color='red', fontweight='bold')

    plt.tight_layout()
    plt.savefig('combined-layers-dependencies.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("Created: combined-layers-dependencies.png")


if __name__ == '__main__':
    # Change to images directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print("Generating layers and dependencies diagrams...")
    # Generate all diagrams (for backward compatibility with docs)
    create_layers_hierarchy_diagram()
    create_dependencies_first_level_diagram()
    create_dependencies_second_level_diagram()
    # Combined diagram is the main one - shows everything in one place
    create_combined_layers_diagram()
    print("Done!")
    print("\nNote: combined-layers-dependencies.png is the main diagram showing everything.")
