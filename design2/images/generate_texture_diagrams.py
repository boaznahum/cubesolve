"""
Generate diagrams for the Texture Drawing Flow documentation.
Creates class diagram and sequence diagram for texture rendering.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, ConnectionPatch
import os

# Color scheme for layers
LAYER_COLORS = {
    'event_loop': '#E8F4E8',    # Light Green
    'window': '#E8E8F4',         # Light Blue
    'viewer': '#F4E8E8',         # Light Pink
    'renderer': '#F4F4E8',       # Light Yellow
    'types': '#F0F0F0',          # Light Gray
}


def create_texture_classes_diagram():
    """Create class diagram for texture drawing components."""
    fig, ax = plt.subplots(1, 1, figsize=(18, 14))
    ax.set_xlim(-1, 19)
    ax.set_ylim(-1, 15)
    ax.set_aspect('equal')
    ax.axis('off')

    fig.suptitle('Texture Drawing - Class Diagram', fontsize=16, fontweight='bold', y=0.97)

    # === EVENT LOOP LAYER ===
    ax.add_patch(FancyBboxPatch((0, 12), 4, 2.5, boxstyle="round,pad=0.1",
                                 facecolor=LAYER_COLORS['event_loop'], edgecolor='black', linewidth=2))
    ax.text(2, 14.1, 'Event Loop Layer', ha='center', va='center', fontsize=10, fontweight='bold')

    # PygletEventLoop class
    ax.add_patch(FancyBboxPatch((0.2, 12.2), 3.6, 1.7, boxstyle="round,pad=0.05",
                                 facecolor='white', edgecolor='#666'))
    ax.text(2, 13.6, 'PygletEventLoop', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(2, 13.1, '+run()', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(2, 12.7, '+schedule_interval()', ha='center', va='center', fontsize=7, family='monospace')

    # === WINDOW LAYER ===
    ax.add_patch(FancyBboxPatch((5, 10), 8, 4.5, boxstyle="round,pad=0.1",
                                 facecolor=LAYER_COLORS['window'], edgecolor='black', linewidth=2))
    ax.text(9, 14.1, 'Window Layer', ha='center', va='center', fontsize=10, fontweight='bold')

    # PygletWindow class
    ax.add_patch(FancyBboxPatch((5.2, 12.2), 3.3, 1.7, boxstyle="round,pad=0.05",
                                 facecolor='white', edgecolor='#666'))
    ax.text(6.85, 13.6, 'PygletWindow', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(6.85, 13.1, '+on_draw()', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(6.85, 12.7, '-_parent: AppWindow', ha='center', va='center', fontsize=7, family='monospace')

    # PygletAppWindow class
    ax.add_patch(FancyBboxPatch((9, 10.2), 3.8, 3.7, boxstyle="round,pad=0.05",
                                 facecolor='white', edgecolor='#666'))
    ax.text(10.9, 13.6, 'PygletAppWindow', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(10.9, 13.1, '-_modern_viewer', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(10.9, 12.7, '-TEXTURE_SETS: list', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(10.9, 12.3, '+on_draw()', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(10.9, 11.9, '+load_texture_set()', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(10.9, 11.5, '+cycle_texture_set()', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(10.9, 11.1, '-_load_current_texture_set()', ha='center', va='center', fontsize=6, family='monospace')

    # === VIEWER LAYER ===
    ax.add_patch(FancyBboxPatch((0, 4), 9, 6, boxstyle="round,pad=0.1",
                                 facecolor=LAYER_COLORS['viewer'], edgecolor='black', linewidth=2))
    ax.text(4.5, 9.6, 'Viewer Layer', ha='center', va='center', fontsize=10, fontweight='bold')

    # ModernGLCubeViewer class
    ax.add_patch(FancyBboxPatch((0.2, 5.5), 4.3, 3.8, boxstyle="round,pad=0.05",
                                 facecolor='white', edgecolor='#666'))
    ax.text(2.35, 9.0, 'ModernGLCubeViewer', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(2.35, 8.5, '-_texture_mode: bool', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(2.35, 8.1, '-_face_textures: dict', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(2.35, 7.7, '-_triangles_per_color: dict', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(2.35, 7.3, '-_dirty: bool', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(2.35, 6.9, '+draw()', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(2.35, 6.5, '+set_texture_mode()', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(2.35, 6.1, '+load_texture_set()', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(2.35, 5.7, '+load_face_texture()', ha='center', va='center', fontsize=7, family='monospace')

    # ModernGLBoard class
    ax.add_patch(FancyBboxPatch((5, 6.5), 3.8, 2.5, boxstyle="round,pad=0.05",
                                 facecolor='white', edgecolor='#666'))
    ax.text(6.9, 8.7, 'ModernGLBoard', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(6.9, 8.2, '-_faces: dict[FaceName, Face]', ha='center', va='center', fontsize=6, family='monospace')
    ax.text(6.9, 7.8, '+generate_geometry()', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(6.9, 7.4, '+generate_textured_geometry()', ha='center', va='center', fontsize=6, family='monospace')

    # ModernGLFace class
    ax.add_patch(FancyBboxPatch((5, 4.2), 3.8, 1.8, boxstyle="round,pad=0.05",
                                 facecolor='white', edgecolor='#666'))
    ax.text(6.9, 5.7, 'ModernGLFace', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(6.9, 5.2, '+generate_triangles()', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(6.9, 4.8, '+generate_triangles_by_color()', ha='center', va='center', fontsize=6, family='monospace')

    # === RENDERER LAYER ===
    ax.add_patch(FancyBboxPatch((10, 2), 8, 7, boxstyle="round,pad=0.1",
                                 facecolor=LAYER_COLORS['renderer'], edgecolor='black', linewidth=2))
    ax.text(14, 8.6, 'Renderer Layer', ha='center', va='center', fontsize=10, fontweight='bold')

    # ModernGLRenderer class
    ax.add_patch(FancyBboxPatch((10.2, 2.2), 7.6, 6.2, boxstyle="round,pad=0.05",
                                 facecolor='white', edgecolor='#666'))
    ax.text(14, 8.1, 'ModernGLRenderer', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(14, 7.6, '-_textures: dict[int, c_uint]', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(14, 7.2, '-_next_texture_handle: int', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(14, 6.8, '-_bound_texture: int | None', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(14, 6.4, '-_textured_vao: c_uint', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(14, 6.0, '-_textured_shader: ShaderProgram', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(14, 5.5, '+load_texture(path) -> handle', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(14, 5.1, '+bind_texture(handle)', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(14, 4.7, '+delete_texture(handle)', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(14, 4.3, '+draw_textured_lit_triangles()', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(14, 3.9, '+draw_lit_triangles()', ha='center', va='center', fontsize=7, family='monospace')

    # === TYPES ===
    ax.add_patch(FancyBboxPatch((0, 0), 9, 3, boxstyle="round,pad=0.1",
                                 facecolor=LAYER_COLORS['types'], edgecolor='black', linewidth=2))
    ax.text(4.5, 2.7, 'Types', ha='center', va='center', fontsize=10, fontweight='bold')

    # Type boxes
    ax.add_patch(FancyBboxPatch((0.2, 0.3), 2.5, 2, boxstyle="round,pad=0.03",
                                 facecolor='white', edgecolor='#666'))
    ax.text(1.45, 2.0, 'TextureHandle', ha='center', va='center', fontsize=8, fontweight='bold')
    ax.text(1.45, 1.5, '= int', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(1.45, 1.0, '(opaque handle)', ha='center', va='center', fontsize=6, style='italic')

    ax.add_patch(FancyBboxPatch((3, 0.3), 2.8, 2, boxstyle="round,pad=0.03",
                                 facecolor='white', edgecolor='#666'))
    ax.text(4.4, 2.0, 'FaceName', ha='center', va='center', fontsize=8, fontweight='bold')
    ax.text(4.4, 1.5, 'F|B|R|L|U|D', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(4.4, 1.0, '(enum)', ha='center', va='center', fontsize=6, style='italic')

    ax.add_patch(FancyBboxPatch((6.1, 0.3), 2.7, 2, boxstyle="round,pad=0.03",
                                 facecolor='white', edgecolor='#666'))
    ax.text(7.45, 2.0, 'Color', ha='center', va='center', fontsize=8, fontweight='bold')
    ax.text(7.45, 1.5, 'W|Y|R|O|B|G', ha='center', va='center', fontsize=7, family='monospace')
    ax.text(7.45, 1.0, '(enum)', ha='center', va='center', fontsize=6, style='italic')

    # === ARROWS (relationships) ===

    # Event loop triggers window
    ax.annotate('', xy=(5.2, 13.0), xytext=(3.8, 13.0),
                arrowprops=dict(arrowstyle='->', color='#666', lw=1.5, linestyle='dashed'))
    ax.text(4.5, 13.3, 'triggers', ha='center', va='center', fontsize=7, style='italic')

    # PygletWindow delegates to PygletAppWindow
    ax.annotate('', xy=(9.0, 12.8), xytext=(8.5, 12.8),
                arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))
    ax.text(8.75, 13.1, 'delegates', ha='center', va='center', fontsize=6, style='italic')

    # AppWindow -> ModernGLCubeViewer
    ax.annotate('', xy=(4.5, 8.5), xytext=(9.0, 11.0),
                arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))
    ax.text(6.0, 10.2, 'draw()', ha='center', va='center', fontsize=7, style='italic')

    # ModernGLCubeViewer -> ModernGLBoard
    ax.annotate('', xy=(5.0, 7.5), xytext=(4.5, 7.5),
                arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))

    # ModernGLBoard -> ModernGLFace
    ax.annotate('', xy=(6.9, 6.0), xytext=(6.9, 6.5),
                arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))
    ax.text(7.5, 6.25, 'contains 6', ha='left', va='center', fontsize=6, style='italic')

    # ModernGLCubeViewer -> ModernGLRenderer
    ax.annotate('', xy=(10.2, 5.5), xytext=(4.5, 7.0),
                arrowprops=dict(arrowstyle='->', color='blue', lw=2))
    ax.text(7.5, 5.8, 'draw_textured_lit_triangles()', ha='center', va='center',
            fontsize=7, style='italic', color='blue')

    # AppWindow -> ModernGLRenderer (via viewer)
    ax.annotate('', xy=(10.2, 7.0), xytext=(9.0, 10.5),
                arrowprops=dict(arrowstyle='->', color='#666', lw=1.5, linestyle='dotted'))

    # === NOTES ===
    ax.add_patch(FancyBboxPatch((14, 0.2), 4.8, 1.5, boxstyle="round,pad=0.1",
                                 facecolor='#FFFACD', edgecolor='#DAA520', linewidth=1))
    ax.text(16.4, 1.4, 'Texture handles are', ha='center', va='center', fontsize=7)
    ax.text(16.4, 1.0, 'internal IDs mapped to', ha='center', va='center', fontsize=7)
    ax.text(16.4, 0.6, 'OpenGL texture IDs', ha='center', va='center', fontsize=7)

    plt.tight_layout()
    plt.savefig('texture-drawing-classes.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("Created: texture-drawing-classes.png")


def create_texture_sequence_diagram():
    """Create sequence diagram for texture frame rendering."""
    fig, ax = plt.subplots(1, 1, figsize=(18, 16))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 17)
    ax.set_aspect('equal')
    ax.axis('off')

    fig.suptitle('Texture Drawing - Sequence Diagram (Frame Rendering)', fontsize=14, fontweight='bold', y=0.98)

    # Participant positions
    participants = {
        'pyglet': (1.5, 'pyglet.app', '#E8F4E8'),
        'eventloop': (4, 'PygletEventLoop', '#E8F4E8'),
        'window': (6.5, 'PygletWindow', '#E8E8F4'),
        'appwindow': (9, 'PygletAppWindow', '#E8E8F4'),
        'viewer': (11.5, 'ModernGLCubeViewer', '#F4E8E8'),
        'board': (14, 'ModernGLBoard', '#F4E8E8'),
        'renderer': (16.5, 'ModernGLRenderer', '#F4F4E8'),
    }

    # Draw participant boxes at top
    for key, (x, label, color) in participants.items():
        ax.add_patch(FancyBboxPatch((x-0.9, 15.5), 1.8, 1, boxstyle="round,pad=0.05",
                                     facecolor=color, edgecolor='black', linewidth=1.5))
        ax.text(x, 16, label, ha='center', va='center', fontsize=7, fontweight='bold')

    # Draw lifelines
    for key, (x, _, _) in participants.items():
        ax.plot([x, x], [0.5, 15.5], color='#AAA', linestyle='--', linewidth=1)

    # Helper for messages
    def msg(from_p, to_p, y, text, response=False, color='#333'):
        x1 = participants[from_p][0]
        x2 = participants[to_p][0]
        style = '<-' if response else '->'
        ax.annotate('', xy=(x2, y), xytext=(x1, y),
                    arrowprops=dict(arrowstyle=style, color=color, lw=1.5))
        mid = (x1 + x2) / 2
        ax.text(mid, y + 0.25, text, ha='center', va='center', fontsize=6)

    def activation(p, y_start, y_end, color='#DDD'):
        x = participants[p][0]
        ax.add_patch(FancyBboxPatch((x-0.15, y_end), 0.3, y_start-y_end,
                                     facecolor=color, edgecolor='#666', linewidth=0.5))

    def note(x, y, text, width=2.5):
        ax.add_patch(FancyBboxPatch((x, y-0.3), width, 0.6, boxstyle="round,pad=0.05",
                                     facecolor='#FFFACD', edgecolor='#DAA520', linewidth=1))
        ax.text(x + width/2, y, text, ha='center', va='center', fontsize=5)

    def section(y, label):
        ax.plot([0.3, 17.7], [y, y], color='#666', linestyle='-', linewidth=0.5)
        ax.add_patch(FancyBboxPatch((0.3, y-0.15), 2.5, 0.3, facecolor='#EEE', edgecolor='#666'))
        ax.text(1.55, y, label, ha='center', va='center', fontsize=6, fontweight='bold')

    # === SEQUENCE ===
    y = 15

    # Event loop running
    section(y, 'Event Loop')
    y -= 0.8

    msg('eventloop', 'pyglet', y, 'run()')
    activation('pyglet', y, 0.5, '#C8E6C9')
    y -= 0.6

    note(0.3, y, 'loop every frame', 2)
    y -= 0.8

    # on_draw
    section(y, 'on_draw Event')
    y -= 0.6

    msg('pyglet', 'window', y, 'on_draw()')
    activation('window', y, y-0.8, '#BBDEFB')
    y -= 0.5

    msg('window', 'appwindow', y, 'on_draw()')
    activation('appwindow', y, y-6.5, '#BBDEFB')
    y -= 0.8

    # Scene setup
    section(y, 'Scene Setup')
    y -= 0.6

    note(9-0.9, y, 'glClearColor, glClear', 2.5)
    y -= 0.5
    note(9-0.9, y, 'setup view transforms', 2.5)
    y -= 0.8

    # Cube drawing
    section(y, 'Cube Drawing')
    y -= 0.6

    msg('appwindow', 'viewer', y, 'draw()')
    activation('viewer', y, y-4.5, '#FFCDD2')
    y -= 0.6

    # Dirty check
    note(11.5-0.9, y, 'if dirty:', 1.5)
    y -= 0.5

    msg('viewer', 'board', y, 'generate_geometry()')
    activation('board', y, y-0.3, '#FFCDD2')
    y -= 0.3
    msg('board', 'viewer', y, 'triangles_per_color', response=True)
    y -= 0.6

    # Texture loop
    note(11.5-0.9, y, 'for each Color:', 2)
    y -= 0.5

    note(11.5-0.9, y, 'face = COLOR_TO_FACE[c]', 2.5)
    y -= 0.4
    note(11.5-0.9, y, 'tex = _face_textures[face]', 2.5)
    y -= 0.6

    msg('viewer', 'renderer', y, 'draw_textured_lit_triangles(triangles, tex)', color='blue')
    activation('renderer', y, y-2.2, '#FFF9C4')
    y -= 0.5

    # OpenGL operations
    section(y, 'OpenGL Texture Ops')
    y -= 0.5

    note(16.5-1.2, y, 'glUseProgram(shader)', 2.4)
    y -= 0.35
    note(16.5-1.2, y, 'set uniforms (MVP, light)', 2.4)
    y -= 0.35
    note(16.5-1.2, y, 'glActiveTexture(GL_TEXTURE0)', 2.4)
    y -= 0.35
    note(16.5-1.2, y, 'glBindTexture(GL_TEXTURE_2D, id)', 2.4)
    y -= 0.35
    note(16.5-1.2, y, 'glBindVertexArray(vao)', 2.4)
    y -= 0.35
    note(16.5-1.2, y, 'glDrawArrays(GL_TRIANGLES)', 2.4)
    y -= 0.5

    msg('renderer', 'viewer', y, '', response=True)
    y -= 0.5

    note(11.5-0.9, y, 'draw_colored_lines()', 2.2)
    y -= 0.5

    msg('viewer', 'appwindow', y, '', response=True)
    y -= 0.6

    # Additional rendering
    section(y, 'Additional Rendering')
    y -= 0.5

    note(9-0.9, y, 'animation (if active)', 2.2)
    y -= 0.4
    note(9-0.9, y, 'celebration (if active)', 2.2)
    y -= 0.4
    note(9-0.9, y, 'text labels', 2.2)

    plt.tight_layout()
    plt.savefig('texture-drawing-sequence.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("Created: texture-drawing-sequence.png")


def create_texture_loading_sequence():
    """Create sequence diagram for texture loading."""
    fig, ax = plt.subplots(1, 1, figsize=(16, 14))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 15)
    ax.set_aspect('equal')
    ax.axis('off')

    fig.suptitle('Texture Loading - Sequence Diagram', fontsize=14, fontweight='bold', y=0.98)

    # Participant positions
    participants = {
        'appwindow': (2, 'PygletAppWindow', '#E8E8F4'),
        'viewer': (5, 'ModernGLCubeViewer', '#F4E8E8'),
        'renderer': (8, 'ModernGLRenderer', '#F4F4E8'),
        'pygletimg': (11, 'pyglet.image', '#E8F4E8'),
        'opengl': (14, 'OpenGL', '#FFF9C4'),
    }

    # Draw participant boxes
    for key, (x, label, color) in participants.items():
        ax.add_patch(FancyBboxPatch((x-1, 13.5), 2, 1, boxstyle="round,pad=0.05",
                                     facecolor=color, edgecolor='black', linewidth=1.5))
        ax.text(x, 14, label, ha='center', va='center', fontsize=8, fontweight='bold')

    # Draw lifelines
    for key, (x, _, _) in participants.items():
        ax.plot([x, x], [0.5, 13.5], color='#AAA', linestyle='--', linewidth=1)

    def msg(from_p, to_p, y, text, response=False, color='#333'):
        x1 = participants[from_p][0]
        x2 = participants[to_p][0]
        style = '<-' if response else '->'
        ax.annotate('', xy=(x2, y), xytext=(x1, y),
                    arrowprops=dict(arrowstyle=style, color=color, lw=1.5))
        mid = (x1 + x2) / 2
        ax.text(mid, y + 0.2, text, ha='center', va='center', fontsize=6)

    def activation(p, y_start, y_end, color='#DDD'):
        x = participants[p][0]
        ax.add_patch(FancyBboxPatch((x-0.15, y_end), 0.3, y_start-y_end,
                                     facecolor=color, edgecolor='#666', linewidth=0.5))

    def note(x, y, text, width=2.5):
        ax.add_patch(FancyBboxPatch((x, y-0.25), width, 0.5, boxstyle="round,pad=0.05",
                                     facecolor='#FFFACD', edgecolor='#DAA520', linewidth=1))
        ax.text(x + width/2, y, text, ha='center', va='center', fontsize=5)

    def section(y, label):
        ax.plot([0.3, 15.7], [y, y], color='#666', linestyle='-', linewidth=0.5)
        ax.add_patch(FancyBboxPatch((0.3, y-0.15), 3, 0.3, facecolor='#EEE', edgecolor='#666'))
        ax.text(1.8, y, label, ha='center', va='center', fontsize=6, fontweight='bold')

    y = 13

    # Texture Set Loading
    section(y, 'Texture Set Loading')
    y -= 0.7

    note(2-1, y, '_load_current_texture_set()', 2.8)
    activation('appwindow', y, y-1.5, '#BBDEFB')
    y -= 0.5

    note(2-1, y, 'path = TEXTURE_SETS[idx]', 2.8)
    y -= 0.7

    msg('appwindow', 'viewer', y, 'load_texture_set(directory)')
    activation('viewer', y, y-8, '#FFCDD2')
    y -= 0.7

    # Loop for each face
    section(y, 'For Each Face (F,B,R,L,U,D)')
    y -= 0.6

    note(5-1, y, 'find {face}.{png,jpg,...}', 2.5)
    y -= 0.5

    msg('viewer', 'viewer', y-0.2, 'load_face_texture(face, path)')
    y -= 0.6

    msg('viewer', 'renderer', y, 'load_texture(file_path)')
    activation('renderer', y, y-5.5, '#FFF9C4')
    y -= 0.7

    # Image loading
    section(y, 'Image Loading')
    y -= 0.5

    msg('renderer', 'pygletimg', y, 'load(file_path)')
    activation('pygletimg', y, y-0.3, '#C8E6C9')
    y -= 0.3
    msg('pygletimg', 'renderer', y, 'image', response=True)
    y -= 0.5

    note(8-1.2, y, 'image_data = image.get_image_data()', 3)
    y -= 0.6

    # OpenGL texture creation
    section(y, 'OpenGL Texture Creation')
    y -= 0.5

    msg('renderer', 'opengl', y, 'glGenTextures(1)')
    y -= 0.3
    msg('opengl', 'renderer', y, 'tex_id', response=True)
    y -= 0.5

    msg('renderer', 'opengl', y, 'glBindTexture(GL_TEXTURE_2D, tex_id)')
    y -= 0.5

    msg('renderer', 'opengl', y, 'glTexParameteri(...)')
    note(14-1, y-0.3, 'MIN, MAG, WRAP', 2)
    y -= 0.6

    msg('renderer', 'opengl', y, 'glTexImage2D(...)')
    note(14-1, y-0.3, 'upload pixel data', 2)
    y -= 0.6

    msg('renderer', 'opengl', y, 'glGenerateMipmap()')
    y -= 0.6

    # Handle assignment
    section(y, 'Handle Assignment')
    y -= 0.5

    note(8-1.2, y, 'handle = _next_texture_handle++', 3)
    y -= 0.4
    note(8-1.2, y, '_textures[handle] = tex_id', 3)
    y -= 0.5

    msg('renderer', 'viewer', y, 'handle', response=True)
    y -= 0.5

    note(5-1.2, y, '_face_textures[face] = handle', 3)
    y -= 0.4
    note(5-1.2, y, '_dirty = True', 2)
    y -= 0.5

    msg('viewer', 'appwindow', y, 'count', response=True)

    plt.tight_layout()
    plt.savefig('texture-loading-sequence.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("Created: texture-loading-sequence.png")


if __name__ == '__main__':
    # Change to images directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print("Generating texture drawing diagrams...")
    create_texture_classes_diagram()
    create_texture_sequence_diagram()
    create_texture_loading_sequence()
    print("Done!")
