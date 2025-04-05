from flet import (
    Column,
    Container,
    Page,
    Colors,
    ElevatedButton,
    Row,
    FilePickerResultEvent,
    FilePicker,
    AlertDialog,
    Text,
    TextButton,
    Dropdown,
    dropdown
)
from table import Table
from body import Body
from ifc_data import IfcData
from pie_chart import PieChart
from shared_resources import SharedResources

class ControlsColumn(Container):
    def __init__(self, page: Page, body: Body, width: int = None):
        self.page = page
        super().__init__()
        
        self.width = width
        self.body = body
        
        self.data_loaded = False    
        self.added_pieChart = False
        self.added_table = False
        
        self.total_cost_text = Text("Suma kosztów: 0.00")
        SharedResources.set_total_cost_text(self.total_cost_text)
        
        # file picker for IFC file
        def pick_file_result(e: FilePickerResultEvent):
            if e.files:
                try:
                    IfcData.load(e.files[0].path)
                    self.data_loaded = True
                    self.body.add_content(Table())
                    self.added_table = True
                    self.__refresh_toggle_button_label(True)
                    # Set "No chart" option in Dropdown
                    self.show_pie_chart_dropdown.value = "none"
                    self.show_pie_chart_dropdown.update()
                    self.__show_pie_chart(None)
                except Exception as e:
                    self.__display_alert("Błąd wczytywania pliku", str(e))
                    self.data_loaded = False
                    self.body.delete_content('left')
                
                
        self.file_picker = FilePicker(on_result=pick_file_result)
        page.overlay.append(self.file_picker)
        
        self.load_ifc_data_button = ElevatedButton(
            "Wczytaj model IFC", on_click=self.__on_click_load_ifc_data,
            icon='upload'
        )
        
        self.toggle_table_button = ElevatedButton(
            "Pokaż tabelę", on_click=self.__toggle_table_visibility,
            icon='table_chart'
        )
        
        self.change_table_type_button = ElevatedButton(
            "Pokaż tabelę elementów", on_click=self.__change_table_type,
            icon='swap_horiz', disabled=True
        )
        
        self.show_pie_chart_dropdown = Dropdown(
            options=[
                dropdown.Option("none", "Brak wykresu"),
                dropdown.Option("material_cost", "Wykres kosztów materiałów"),
                dropdown.Option("element_cost", "Wykres kosztów elementów"),
                dropdown.Option("material_volume", "Wykres objętości materiałów"),
                dropdown.Option("element_volume", "Wykres objętości elementów")
            ],
            value="none",
            on_change=self.__show_pie_chart
        )
        
        controls = [
            self.load_ifc_data_button,
            self.toggle_table_button,
            self.change_table_type_button,
            self.show_pie_chart_dropdown,
            self.total_cost_text,
        ]
        
        # Set each control to Row to expand them horizontally
        for i in range(len(controls)):
            control = controls[i]
            control.expand = True
            controls[i] = Row([control])
            
        # adding Container to the top of the column to push the controls down
        controls.insert(0, Container(height=30))
        
        self.content = Column(
            controls,
            horizontal_alignment="center",
        )
        
        
    def __on_click_load_ifc_data(self, e):
        self.file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=['ifc'],
            dialog_title='Wybierz plik IFC'
        )
            
    def __display_alert(self, title: str, message: str):
        dlg = AlertDialog(
            title=Text(title),
            content=Text(message),
            actions=[
                TextButton("OK", on_click=lambda e: self.page.close(dlg))
            ],
        )
        self.page.open(dlg)
        
    def __refresh_toggle_button_label(self, show: bool):
        if show:
            self.toggle_table_button.text = "Ukryj tabelę"
            self.change_table_type_button.disabled = False
        else:
            self.toggle_table_button.text = "Pokaż tabelę"
            self.change_table_type_button.disabled = True
        self.toggle_table_button.update()
        self.change_table_type_button.update()
            
        
    def __toggle_table_visibility(self, e):
        if not self.data_loaded:
            self.__display_alert("Brak danych", "Wczytaj plik IFC przed pokazaniem tabeli.")
            return
        
        if self.added_table:
            self.body.delete_content('left')
            self.added_table = False
            self.__refresh_toggle_button_label(False)
        else:
            self.body.add_content(Table())
            self.added_table = True
            self.__refresh_toggle_button_label(True)
            SharedResources.update_total_cost(IfcData.get_total_cost())
            
    def __change_table_type(self, e):
        if not self.added_table:
            return
        
        current_table = self.body.get_control('left')
        if isinstance(current_table, Table):
            new_type = "element" if current_table.table.type == "material" else "material"
            self.body.delete_content('left', auto_update=False)
            self.body.add_content(Table(new_type), auto_update=False)
            self.body.update()
            self.change_table_type_button.text = "Pokaż tabelę materiałów" if new_type == "element" else "Pokaż tabelę elementów"
            self.change_table_type_button.update()
            
    def __show_pie_chart(self, e):
        selected_option = self.show_pie_chart_dropdown.value
        if selected_option == "none":
            self.body.delete_content('right')
            self.added_pieChart = False
        else:
            type, type_attr = selected_option.split('_')
            if IfcData.can_create_pie_chart(type, type_attr):
                self.body.add_content(PieChart(type, type_attr), side='right')
                self.added_pieChart = True
            else:
                info = IfcData.get_pie_chart_error_message(type, type_attr)
                self.__display_alert("Błąd wykresu", info)
                self.show_pie_chart_dropdown.value = "none"
                self.show_pie_chart_dropdown.update()

