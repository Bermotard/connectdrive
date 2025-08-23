"""
Style configuration for the Network Drive Mounter application.
"""
from tkinter import ttk
from .theme import get_theme

def apply_styles(root):
    """Apply custom styles to the application."""
    theme = get_theme()
    colors = theme['colors']
    fonts = theme['fonts']
    sizes = theme['sizes']
    
    style = ttk.Style()
    
    # Configure the theme
    style.theme_use('clam')
    
    # Base styles
    style.configure('.',
                  background=colors['bg'],
                  foreground=colors['fg'],
                  fieldbackground=colors['entry_bg'],
                  selectbackground=colors['accent'],
                  selectforeground=colors['fg'],
                  insertcolor=colors['fg'],
                  highlightthickness=0,
                  borderwidth=sizes['border_width'],
                  relief='flat',
                  font=fonts['default'])
    
    # Frame styles
    style.configure('TFrame', background=colors['bg'])
    style.configure('TLabel', background=colors['bg'], foreground=colors['fg'])
    
    # Button styles
    style.configure('TButton',
                  background=colors['button_bg'],
                  foreground=colors['button_fg'],
                  padding=(sizes['padding'] * 2, sizes['padding']),
                  font=fonts['default'])
    
    style.map('TButton',
             background=[('active', colors['accent_hover']), 
                       ('pressed', colors['accent_hover'])],
             foreground=[('active', colors['button_fg']), 
                       ('pressed', colors['button_fg'])])
    
    # Entry and combobox styles
    style.configure('TEntry',
                  fieldbackground=colors['entry_bg'],
                  foreground=colors['fg'],
                  insertcolor=colors['fg'],
                  borderwidth=sizes['border_width'],
                  relief='solid',
                  padding=sizes['padding'])
    
    style.configure('TCombobox',
                  fieldbackground=colors['entry_bg'],
                  background=colors['entry_bg'],
                  foreground=colors['fg'],
                  selectbackground=colors['accent'],
                  selectforeground=colors['fg'],
                  arrowcolor=colors['fg'],
                  borderwidth=sizes['border_width'],
                  relief='solid',
                  padding=sizes['padding'])
    
    # Tab styles
    style.configure('TNotebook', background=colors['bg'])
    style.configure('TNotebook.Tab',
                  background=colors['tab_bg'],
                  foreground=colors['fg'],
                  padding=(sizes['padding'] * 2, sizes['padding'] // 2),
                  font=fonts['bold'])
    
    style.map('TNotebook.Tab',
             background=[('selected', colors['accent']), 
                       ('active', colors['accent_hover'])],
             foreground=[('selected', colors['fg']), 
                       ('active', colors['fg'])])
    
    # Treeview styles
    style.configure('Treeview',
                  background=colors['entry_bg'],
                  foreground=colors['fg'],
                  fieldbackground=colors['entry_bg'],
                  borderwidth=0,
                  rowheight=25)
    
    style.map('Treeview',
             background=[('selected', colors['accent'])],
             foreground=[('selected', colors['fg'])])
    
    # Scrollbar styles
    style.configure('Vertical.TScrollbar',
                  background=colors['entry_bg'],
                  troughcolor=colors['bg'],
                  bordercolor=colors['bg'],
                  arrowcolor=colors['fg'],
                  arrowsize=12)
    
    # Menu styles
    root.option_add('*Menu.background', colors['bg'])
    root.option_add('*Menu.foreground', colors['fg'])
    root.option_add('*Menu.activeBackground', colors['accent'])
    root.option_add('*Menu.activeForeground', colors['fg'])
    root.option_add('*Menu.borderWidth', 0)
    root.option_add('*Menu.relief', 'flat')
    
    # Custom styles
    style.configure('Success.TButton', background=colors['success'])
    style.configure('Warning.TButton', background=colors['warning'])
    style.configure('Error.TButton', background=colors['error'])
    
    return style
