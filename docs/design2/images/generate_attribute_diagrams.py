#!/usr/bin/env python3
"""Generate diagrams for PartEdge Attribute System documentation."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# Set up style
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10


def create_attribute_overview():
    """Create overview diagram showing all three attribute types."""
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    ax.set_aspect('equal')

    # Title
    ax.text(7, 9.5, 'PartEdge Attribute System', fontsize=18, fontweight='bold',
            ha='center', va='center')

    # Central PartEdge box
    pe_box = FancyBboxPatch((5, 4.5), 4, 2, boxstyle="round,pad=0.1",
                             facecolor='#E3F2FD', edgecolor='#1565C0', linewidth=2)
    ax.add_patch(pe_box)
    ax.text(7, 5.5, 'PartEdge', fontsize=14, fontweight='bold', ha='center', va='center')
    ax.text(7, 4.9, '(smallest cube unit)', fontsize=9, ha='center', va='center', style='italic')

    # attributes box (top)
    attr_box = FancyBboxPatch((1, 7), 4, 2, boxstyle="round,pad=0.1",
                               facecolor='#FFF3E0', edgecolor='#E65100', linewidth=2)
    ax.add_patch(attr_box)
    ax.text(3, 8.3, 'attributes', fontsize=12, fontweight='bold', ha='center', va='center',
            fontfamily='monospace', color='#E65100')
    ax.text(3, 7.7, 'Structural', fontsize=10, ha='center', va='center')
    ax.text(3, 7.3, 'origin, on_x, on_y, cw', fontsize=8, ha='center', va='center',
            fontfamily='monospace')

    # Arrow from attributes to PartEdge
    ax.annotate('', xy=(5, 5.5), xytext=(5, 7),
                arrowprops=dict(arrowstyle='->', color='#E65100', lw=2))
    ax.text(4.5, 6.3, 'FIXED', fontsize=9, ha='center', va='center', color='#E65100',
            fontweight='bold', rotation=90)

    # c_attributes box (left)
    c_box = FancyBboxPatch((0.5, 1.5), 4, 2, boxstyle="round,pad=0.1",
                            facecolor='#E8F5E9', edgecolor='#2E7D32', linewidth=2)
    ax.add_patch(c_box)
    ax.text(2.5, 2.8, 'c_attributes', fontsize=12, fontweight='bold', ha='center', va='center',
            fontfamily='monospace', color='#2E7D32')
    ax.text(2.5, 2.3, 'Color-Associated', fontsize=10, ha='center', va='center')
    ax.text(2.5, 1.8, 'trackers, VMarker.C1', fontsize=8, ha='center', va='center',
            fontfamily='monospace')

    # Arrow from c_attributes to PartEdge
    ax.annotate('', xy=(5.2, 4.7), xytext=(4.3, 3.5),
                arrowprops=dict(arrowstyle='->', color='#2E7D32', lw=2))
    ax.text(3.5, 4.3, 'MOVES', fontsize=9, ha='center', va='center', color='#2E7D32',
            fontweight='bold', rotation=45)

    # f_attributes box (right)
    f_box = FancyBboxPatch((9.5, 1.5), 4, 2, boxstyle="round,pad=0.1",
                            facecolor='#FCE4EC', edgecolor='#C2185B', linewidth=2)
    ax.add_patch(f_box)
    ax.text(11.5, 2.8, 'f_attributes', fontsize=12, fontweight='bold', ha='center', va='center',
            fontfamily='monospace', color='#C2185B')
    ax.text(11.5, 2.3, 'Fixed to Slot', fontsize=10, ha='center', va='center')
    ax.text(11.5, 1.8, 'destinations, VMarker.C2', fontsize=8, ha='center', va='center',
            fontfamily='monospace')

    # Arrow from f_attributes to PartEdge
    ax.annotate('', xy=(8.8, 4.7), xytext=(9.7, 3.5),
                arrowprops=dict(arrowstyle='->', color='#C2185B', lw=2))
    ax.text(10.5, 4.3, 'STAYS', fontsize=9, ha='center', va='center', color='#C2185B',
            fontweight='bold', rotation=-45)

    # Key insight box
    insight_box = FancyBboxPatch((9, 7), 4.5, 2, boxstyle="round,pad=0.1",
                                  facecolor='#FFFDE7', edgecolor='#F9A825', linewidth=2)
    ax.add_patch(insight_box)
    ax.text(11.25, 8.5, 'Key Insight', fontsize=11, fontweight='bold', ha='center', va='center')
    ax.text(11.25, 8, 'During copy_color():', fontsize=9, ha='center', va='center',
            fontfamily='monospace')
    ax.text(11.25, 7.5, 'c_attributes: COPIED', fontsize=9, ha='center', va='center',
            color='#2E7D32', fontweight='bold')
    ax.text(11.25, 7.1, 'f_attributes: NOT copied', fontsize=9, ha='center', va='center',
            color='#C2185B', fontweight='bold')

    # Bottom summary
    ax.text(7, 0.5, 'Track piece → c_attributes  |  Mark destination → f_attributes  |  Slot position → attributes',
            fontsize=10, ha='center', va='center', style='italic',
            bbox=dict(boxstyle='round', facecolor='#F5F5F5', edgecolor='gray'))

    plt.tight_layout()
    plt.savefig('attribute-system-overview.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("Created: attribute-system-overview.png")


def create_animation_tracking():
    """Create diagram showing animation tracking use case."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 7))

    for ax in axes:
        ax.set_xlim(0, 7)
        ax.set_ylim(0, 7)
        ax.axis('off')
        ax.set_aspect('equal')

    # BEFORE ROTATION (left)
    ax = axes[0]
    ax.text(3.5, 6.5, 'BEFORE F Rotation', fontsize=14, fontweight='bold', ha='center')

    # Source slot (has piece to track)
    src_box = FancyBboxPatch((0.5, 2.5), 2.5, 3, boxstyle="round,pad=0.1",
                              facecolor='#FFCDD2', edgecolor='#D32F2F', linewidth=2)
    ax.add_patch(src_box)
    ax.text(1.75, 5, 'RED Sticker', fontsize=11, fontweight='bold', ha='center', color='#D32F2F')
    ax.text(1.75, 4.3, 'c_attributes:', fontsize=9, ha='center', fontfamily='monospace')
    ax.text(1.75, 3.8, '{"track": "X"}', fontsize=9, ha='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#C8E6C9', edgecolor='#2E7D32'))
    ax.text(1.75, 3.1, 'f_attributes: {}', fontsize=9, ha='center', fontfamily='monospace',
            color='gray')

    # Destination slot (marked as target)
    dst_box = FancyBboxPatch((4, 2.5), 2.5, 3, boxstyle="round,pad=0.1",
                              facecolor='#C8E6C9', edgecolor='#388E3C', linewidth=2)
    ax.add_patch(dst_box)
    ax.text(5.25, 5, 'GREEN Sticker', fontsize=11, fontweight='bold', ha='center', color='#388E3C')
    ax.text(5.25, 4.3, 'c_attributes: {}', fontsize=9, ha='center', fontfamily='monospace',
            color='gray')
    ax.text(5.25, 3.8, 'f_attributes:', fontsize=9, ha='center', fontfamily='monospace')
    ax.text(5.25, 3.1, '{"target": "T"}', fontsize=9, ha='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#FCE4EC', edgecolor='#C2185B'))

    # Labels
    ax.text(1.75, 1.8, 'Source\n(tracked)', fontsize=10, ha='center', va='top')
    ax.text(5.25, 1.8, 'Destination\n(marked)', fontsize=10, ha='center', va='top')

    # Arrow showing rotation
    ax.annotate('', xy=(4, 4), xytext=(3, 4),
                arrowprops=dict(arrowstyle='->', color='#1565C0', lw=3))
    ax.text(3.5, 4.5, 'F', fontsize=12, fontweight='bold', ha='center', color='#1565C0')

    # AFTER ROTATION (right)
    ax = axes[1]
    ax.text(3.5, 6.5, 'AFTER F Rotation', fontsize=14, fontweight='bold', ha='center')

    # Source slot now has different color
    src_box2 = FancyBboxPatch((0.5, 2.5), 2.5, 3, boxstyle="round,pad=0.1",
                               facecolor='#BBDEFB', edgecolor='#1976D2', linewidth=2)
    ax.add_patch(src_box2)
    ax.text(1.75, 5, 'BLUE Sticker', fontsize=11, fontweight='bold', ha='center', color='#1976D2')
    ax.text(1.75, 4.3, 'c_attributes: {}', fontsize=9, ha='center', fontfamily='monospace',
            color='gray')
    ax.text(1.75, 3.5, '(tracker moved out)', fontsize=8, ha='center', style='italic',
            color='gray')

    # Destination slot now has RED + both attributes
    dst_box2 = FancyBboxPatch((4, 2.5), 2.5, 3, boxstyle="round,pad=0.1",
                               facecolor='#FFCDD2', edgecolor='#D32F2F', linewidth=2)
    ax.add_patch(dst_box2)
    ax.text(5.25, 5.2, 'RED Sticker', fontsize=11, fontweight='bold', ha='center', color='#D32F2F')
    ax.text(5.25, 4.6, 'c_attributes:', fontsize=9, ha='center', fontfamily='monospace')
    ax.text(5.25, 4.1, '{"track": "X"}', fontsize=9, ha='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#C8E6C9', edgecolor='#2E7D32'))
    ax.text(5.25, 3.5, 'f_attributes:', fontsize=9, ha='center', fontfamily='monospace')
    ax.text(5.25, 3, '{"target": "T"}', fontsize=9, ha='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#FCE4EC', edgecolor='#C2185B'))

    # Labels
    ax.text(1.75, 1.8, 'Slot 1', fontsize=10, ha='center', va='top')
    ax.text(5.25, 1.8, 'Slot 2', fontsize=10, ha='center', va='top')

    # Success indicator
    ax.text(5.25, 1.2, 'Tracker arrived at target!', fontsize=10, ha='center',
            fontweight='bold', color='#2E7D32',
            bbox=dict(boxstyle='round', facecolor='#E8F5E9', edgecolor='#2E7D32'))

    # Bottom explanation
    fig.text(0.5, 0.02,
             'c_attributes (green) moved with RED sticker  |  f_attributes (pink) stayed at destination slot',
             fontsize=11, ha='center', style='italic',
             bbox=dict(boxstyle='round', facecolor='#F5F5F5', edgecolor='gray'))

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.1)
    plt.savefig('attribute-animation-tracking.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("Created: attribute-animation-tracking.png")


def create_copy_color_flow():
    """Create diagram showing what happens during copy_color()."""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Title
    ax.text(6, 7.5, 'What Happens During copy_color()', fontsize=16, fontweight='bold', ha='center')

    # Source PartEdge
    src_box = FancyBboxPatch((0.5, 2), 4, 4.5, boxstyle="round,pad=0.1",
                              facecolor='#E3F2FD', edgecolor='#1565C0', linewidth=2)
    ax.add_patch(src_box)
    ax.text(2.5, 6, 'Source PartEdge', fontsize=12, fontweight='bold', ha='center', color='#1565C0')

    ax.text(2.5, 5.3, '_color = RED', fontsize=10, ha='center', fontfamily='monospace')
    ax.text(2.5, 4.7, 'attributes = {cw: 1}', fontsize=9, ha='center', fontfamily='monospace',
            color='#E65100')
    ax.text(2.5, 4.1, 'c_attributes = {n: 2}', fontsize=9, ha='center', fontfamily='monospace',
            color='#2E7D32')
    ax.text(2.5, 3.5, 'f_attributes = {}', fontsize=9, ha='center', fontfamily='monospace',
            color='#C2185B')

    # Target PartEdge (before)
    tgt_box1 = FancyBboxPatch((7.5, 4.5), 4, 2, boxstyle="round,pad=0.1",
                               facecolor='#FFEBEE', edgecolor='#C62828', linewidth=2)
    ax.add_patch(tgt_box1)
    ax.text(9.5, 6, 'Target (BEFORE)', fontsize=11, fontweight='bold', ha='center', color='#C62828')
    ax.text(9.5, 5.3, '_color = BLUE', fontsize=9, ha='center', fontfamily='monospace')
    ax.text(9.5, 4.8, 'f_attributes = {dest: T}', fontsize=9, ha='center', fontfamily='monospace',
            color='#C2185B')

    # Target PartEdge (after)
    tgt_box2 = FancyBboxPatch((7.5, 1), 4, 2.8, boxstyle="round,pad=0.1",
                               facecolor='#E8F5E9', edgecolor='#2E7D32', linewidth=2)
    ax.add_patch(tgt_box2)
    ax.text(9.5, 3.5, 'Target (AFTER)', fontsize=11, fontweight='bold', ha='center', color='#2E7D32')
    ax.text(9.5, 2.9, '_color = RED', fontsize=9, ha='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#FFCDD2', edgecolor='#D32F2F', pad=0.1))
    ax.text(9.5, 2.3, 'c_attributes = {n: 2}', fontsize=9, ha='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#C8E6C9', edgecolor='#2E7D32', pad=0.1))
    ax.text(9.5, 1.7, 'f_attributes = {dest: T}', fontsize=9, ha='center', fontfamily='monospace',
            color='#C2185B')
    ax.text(9.5, 1.2, '(unchanged!)', fontsize=8, ha='center', style='italic', color='#C2185B')

    # Arrow
    ax.annotate('', xy=(7.5, 3.5), xytext=(4.5, 4),
                arrowprops=dict(arrowstyle='->', color='#1565C0', lw=3,
                               connectionstyle='arc3,rad=-0.2'))
    ax.text(6, 4.3, 'copy_color()', fontsize=11, fontweight='bold', ha='center',
            fontfamily='monospace', color='#1565C0')

    # Legend
    ax.text(6, 0.5, 'COPIED: _color, c_attributes  |  NOT COPIED: attributes, f_attributes',
            fontsize=10, ha='center', style='italic',
            bbox=dict(boxstyle='round', facecolor='#FFFDE7', edgecolor='#F9A825'))

    plt.tight_layout()
    plt.savefig('attribute-copy-color-flow.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("Created: attribute-copy-color-flow.png")


if __name__ == '__main__':
    create_attribute_overview()
    create_animation_tracking()
    create_copy_color_flow()
    print("\nAll attribute system diagrams generated!")
