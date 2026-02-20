#!/usr/bin/env python
"""
Script to extract all Material Symbols icons from templates and generate:
1. A Google Fonts URL with only those icons
2. An SVG sprite file

Usage: python scripts/update_icons.py
"""

import re
from pathlib import Path
from collections import defaultdict

def extract_icons_from_file(filepath):
    """Extract icon names from a template file."""
    icons = set()
    content = filepath.read_text(encoding='utf-8')
    
    # Pattern: material-symbols-outlined[^>]*>(\w+)<
    pattern = r'material-symbols-outlined[^>]*>(\w+)<'
    matches = re.findall(pattern, content)
    icons.update(matches)
    
    return icons

def find_all_icons():
    """Scan all templates and collect unique icons."""
    templates_dir = Path('core/templates')
    icons = set()
    icon_locations = defaultdict(list)
    
    for template_file in templates_dir.rglob('*.html'):
        file_icons = extract_icons_from_file(template_file)
        for icon in file_icons:
            icons.add(icon)
            icon_locations[icon].append(str(template_file.relative_to('.')))
    
    return sorted(icons), icon_locations

def generate_fonts_url(icons):
    """Generate Google Fonts URL with text parameter."""
    # Join all icons (Google Fonts text parameter doesn't need separators)
    text_param = ''.join(icons)
    url = f"https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0&text={text_param}"
    return url

def generate_svg_sprite(icons):
    """Generate an SVG sprite with all icons (would need actual SVG paths)."""
    # This is a placeholder - you'd need to fetch actual SVG paths from Material Symbols
    sprite = ['<svg xmlns="http://www.w3.org/2000/svg" style="display:none;">']
    for icon in icons:
        sprite.append(f'  <!-- {icon} -->')
        sprite.append(f'  <symbol id="{icon}" viewBox="0 0 24 24">')
        sprite.append(f'    <!-- SVG path for {icon} would go here -->')
        sprite.append('  </symbol>')
    sprite.append('</svg>')
    return '\n'.join(sprite)

def main():
    print("Scanning templates for Material Symbols icons...\n")
    
    icons, locations = find_all_icons()
    
    print(f"Found {len(icons)} unique icons:\n")
    for icon in icons:
        print(f"  - {icon}")
    
    print(f"\nTotal icons: {len(icons)}")
    
    # Generate optimized font URL
    font_url = generate_fonts_url(icons)
    print(f"\nOptimized Google Fonts URL:")
    print(f"{font_url}\n")
    
    # Save URL to file for easy copy-paste
    output_file = Path('core/static/core/material-icons-url.txt')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(font_url)
    print(f"URL saved to: {output_file}")
    
    # Optionally generate a report
    report_file = Path('icon-usage-report.txt')
    with open(report_file, 'w') as f:
        f.write("Material Symbols Icon Usage Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total unique icons: {len(icons)}\n\n")
        f.write("Icons by file:\n")
        for icon, files in sorted(locations.items()):
            f.write(f"\n{icon}:\n")
            for file in files:
                f.write(f"  - {file}\n")
    
    print(f"Full report saved to: {report_file}")

if __name__ == '__main__':
    main()
