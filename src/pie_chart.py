import matplotlib
import matplotlib.pyplot as plt

from flet.matplotlib_chart import MatplotlibChart

from ifc_data import IfcData

matplotlib.use("svg")

class PieChart(MatplotlibChart):
    def __init__(self, type: str = "material", type_attr: str = "cost"):
        self.fig, self.ax = plt.subplots(figsize=(6, 8))  # Zwiększ wysokość wykresu
        super().__init__(self.fig, transparent=True)

        self.__create_chart(type, type_attr)
        self.type = type
        self.type_attr = type_attr

    def __create_chart(self, type: str = "material", type_attr: str = "cost"):
        assert type in ["material", "element"], 'type must be either "material" or "element"'
        assert type_attr in ["cost", "volume"], 'type_attr must be either "cost" or "volume"'

        data = IfcData.get_data(type, type_attr)
        labels = data.iloc[:, 0].tolist()
        values = data.iloc[:, 1].tolist()

        if sum(values) == 0:
            raise ValueError('Sum of values is zero, cannot create pie chart.')

        wedges, texts, autotexts = self.ax.pie(values, labels=None, autopct='%1.1f%%', startangle=90)
        self.ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        # Add legend below the pie chart
        self.ax.legend(wedges, labels, loc="upper center", bbox_to_anchor=(0.5, 0.17))

        # Adjust the position of the labels to avoid overlap
        for autotext in autotexts:
            autotext.set_fontsize(8)
            autotext.set_bbox(dict(facecolor='white', edgecolor='none', alpha=0.7))

    
    def will_unmount(self):
        plt.close('all')