from flet import (
    Page, 
    AppBar, 
    Colors, 
    Icons, 
    Theme, 
    PopupMenuItem,
    Container,
    Text,
    Row,
    IconButton,
    PopupMenuButton
)
from controls_column import ControlsColumn
from body import Body
from shared_resources import SharedResources

class AppLayout:
    NAV_BAR_PROPORTION = 0.2
    
    def __init__(self, page: Page):
        self.page = page
        # Define the function that will change the theme mode
        def change_theme(e):
            self.page.theme_mode = "light" if self.page.theme_mode == "dark" else "dark"
            app_bar.bgcolor = Colors.SURFACE_TINT
            self.page.update()

        # Define the function that will change the color scheme of the theme
        def on_color_selected(e, color):
            self.page.theme = Theme(color_scheme_seed=color)
            self.page.update()
            
        # Define the function to translating the color names to polish
        def translate_color(color):
            dict_colors = {
                'Red': 'Czerwony',
                'Green': 'Zielony',
                'Blue': 'Niebieski',
                'Yellow': 'Żółty',
                'Cyan': 'Cyjan'
            }
            return dict_colors[color]
        
        # Set the default theme mode
        self.page.theme_mode = "light"
        
        # Define the colors and the color items
        colors = ['Red', 'Green', 'Blue', 'Yellow', 'Cyan']
        color_items = [
            PopupMenuItem(
                content=Row([
                    Container(bgcolor=color, width=20, height=20, border_radius=10),
                    Text(translate_color(color))
                ]),
                on_click=lambda e, c=color: on_color_selected(e, c)
            ) 
            for color in colors
        ]
        # set the default color
        self.page.theme = Theme(color_scheme_seed=colors[-1])

        # Define the app bar
        app_bar = AppBar(
            title=Text(page.title),
            leading=PopupMenuButton(
                icon=Icons.PALETTE,
                items=color_items
            ),
            actions=[
                IconButton(icon=Icons.BRIGHTNESS_6, on_click=change_theme)
            ],
            bgcolor=Colors.PRIMARY,
            color=Colors.ON_PRIMARY,
            toolbar_height=70,
        )

        self.page.appbar = app_bar
        self.body = Body()
        SharedResources.set_body(self.body)
        
        main_row = Row(
            [
                ControlsColumn(self.page, self.body, width=self.page.width * self.NAV_BAR_PROPORTION),
                Container(width=1, bgcolor=Colors.SURFACE_TINT),
                self.body
            ],
            expand=True
        )
        
        
        self.page.add(main_row)        
        
        self.page.update()