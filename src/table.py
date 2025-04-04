from flet import (
    DataTable,
    DataColumn,
    DataRow,
    DataCell,
    Text,
    TextField,
    ListView,
    InputBorder,
)
from ifc_data import IfcData
from shared_resources import SharedResources
from pie_chart import PieChart

class Table(ListView): # it is done like this to make it scrollable
    def __init__(self, type: str = "material"):
        super().__init__()
        self.table = Table_prim(type)
        self.controls = [self.table]

class Table_prim(DataTable):
    def __init__(self, type: str):
        self.type = type
        if self.type == "material":
            self.columns = [
                DataColumn(Text("Materiał")),
                DataColumn(Text("Objętość"), numeric=True),
                DataColumn(Text("Cena jednostkowa"), numeric=True),
                DataColumn(Text("Koszt"), numeric=True), 
            ]
        elif self.type == "element":
            self.columns = [
                DataColumn(Text("Element")),
                DataColumn(Text("Objętość"), numeric=True),
                DataColumn(Text("Koszt"), numeric=True), 
            ]
        else:
            raise ValueError('Invalid type. Must be "material" or "element".')
        super().__init__(columns=self.columns)
        self.__add_data()

    def __update_on_tap(self, e):
        if isinstance(e.control.content, Text):
            e.control.content = TextField(
                value=e.control.content.value, 
                border=InputBorder.NONE,
                on_change=self.__on_text_change
            )
            self.update()
        else:
            e.control.content = Text(e.control.content.value)
            self.update()

    def __update_chart_if_needed(self):
        body = SharedResources.get_body()
        chart = body.get_control('right')
        if chart is None:
            return
        elif isinstance(chart, PieChart):
            type = chart.type
            type_attr = chart.type_attr
            
            body.add_content(PieChart(type, type_attr), side='right')

    def __on_text_change(self, e):
        valid = self.__validate_numeric(e)
        if valid:
            new_price = float(e.control.value)
            material = e.control.parent.data['material']
            volume = e.control.parent.data['volume']
            cost = new_price * volume

            # Update the IfcData material price
            IfcData.update_material_price(material, new_price)

            # Update the cost cell
            for row in self.rows:
                if row.cells[0].content.value == material:
                    row.cells[3].content.value = f"{cost:.2f}"
                    break
            self.update()
            self.__update_chart_if_needed()
            self.__update_total_cost()

    def __validate_numeric(self, e):
        valid = True
        try:
            float(e.control.value)
            e.control.error_text = None
            valid = True
        except ValueError:
            e.control.error_text = "Wprowadź liczbę"
            valid = False
        self.update()
        return valid

    def __add_data(self):
        ifc_data = IfcData()
        if self.type == "material":
            material_costs = ifc_data.get_material_costs()
            self.rows = [
                DataRow(
                cells=[
                    DataCell(Text(row['material'])),
                    DataCell(Text(f"{row['volume']:.2f}")),
                    DataCell(
                        Text(f"{row['price']:.2f}"),
                        show_edit_icon=True,
                        on_tap=self.__update_on_tap,
                        data={'material': row['material'], 'volume': row['volume']},
                    ),
                    DataCell(Text(f"{row['cost']:.2f}")),
                ],
                )
                for _, row in material_costs.iterrows()
            ]
        elif self.type == "element":
            element_costs = ifc_data.get_element_costs()
            self.rows = [
                DataRow(
                cells=[
                    DataCell(Text(row['element'])),
                    DataCell(Text(f"{row['volume']:.2f}")),
                    DataCell(Text(f"{row['cost']:.2f}")),
                ],
                )
                for _, row in element_costs.iterrows()
            ]
        self.__update_total_cost()

    def __update_total_cost(self):
        if self.type == "material":
            total_cost = sum(float(row.cells[3].content.value) for row in self.rows)
        else:
            total_cost = sum(float(row.cells[2].content.value) for row in self.rows)
        SharedResources.update_total_cost(total_cost)
