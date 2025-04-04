import flet as ft
from app_layout import AppLayout

def main(page: ft.Page):
    page.title = "Kosztorysowanie na podstawie danych IFC"
    
    page.window.min_width = 1000
    page.window.min_height = 600
    
    AppLayout(page)

ft.app(main)