"""
Theme configuration for the Network Drive Mounter application.
"""

def get_theme():
    """Return the theme configuration dictionary."""
    return {
        'colors': {
            'bg': '#2d2d2d',
            'fg': '#ffffff',
            'accent': '#4a6da7',
            'accent_hover': '#5a7db8',
            'entry_bg': '#3c3f41',
            'button_bg': '#4a6da7',
            'button_fg': '#ffffff',
            'tab_bg': '#3c3f41',
            'tab_active': '#4a6da7',
            'tab_hover': '#5a7db8',
            'success': '#2e7d32',
            'warning': '#ed6c02',
            'error': '#d32f2f',
        },
        'fonts': {
            'default': ('Segoe UI', 9),
            'bold': ('Segoe UI', 9, 'bold'),
            'title': ('Segoe UI', 12, 'bold'),
        },
        'sizes': {
            'padding': 8,
            'border_radius': 4,
            'border_width': 1,
        }
    }
