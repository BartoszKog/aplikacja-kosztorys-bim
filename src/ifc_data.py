import ifcopenshell
import ifcopenshell.util.element as util_element
import pandas as pd

class IfcData:
    df = pd.DataFrame({
        'element': pd.Series(dtype='str'),
        'material': pd.Series(dtype='str'),
        'volume': pd.Series(dtype='float'),
    })
    material_prices = pd.DataFrame({
        'material': pd.Series(dtype='str'),
        'price': pd.Series(dtype='float'),
    })
    ifc_file = None
    model = None

    @classmethod
    def load(cls, ifc_file):
        cls.ifc_file = ifc_file
        cls.model = ifcopenshell.open(ifc_file)
        cls.__clear_df()
        cls.__update_df()

    @classmethod
    def __clear_df(cls):
        cls.df = pd.DataFrame({
            'element': pd.Series(dtype='str'),
            'material': pd.Series(dtype='str'),
            'volume': pd.Series(dtype='float'),
        })

    @classmethod
    def __get_net_volume_from_element(cls, element):
        psets = util_element.get_psets(element)
        for pset_name, pset in psets.items():
            if 'NetVolume' in pset:
                return pset['NetVolume']
        return None

    @classmethod
    def __update_material_prices(cls, material: str):
        if material not in list(cls.material_prices['material']):
            cls.material_prices = cls.material_prices._append({
                'material': material,
                'price': 0,
            }, ignore_index=True)

    @classmethod
    def update_material_price(cls, material: str, price: float):
        cls.__update_material_prices(material)
        cls.material_prices.loc[cls.material_prices['material'] == material, 'price'] = price

    @classmethod
    def __update_df(cls):
        assert cls.model is not None, 'IFC file not loaded'
        for associates_material in cls.model.by_type('IfcRelAssociatesMaterial'):
            material = associates_material.RelatingMaterial
            for element in associates_material.RelatedObjects:
                volume = cls.__get_net_volume_from_element(element)
                if volume is None:
                    continue
                cls.df = cls.df._append({
                    'element': element.is_a(),
                    'material': material.Name,
                    'volume': volume,
                }, ignore_index=True)
                cls.__update_material_prices(material.Name)

    @classmethod
    def get_material_costs(cls):
        if cls.df.empty:
            return pd.DataFrame()
        
        grouped_df = cls.df.groupby('material', as_index=False).agg({'volume': 'sum'})
        grouped_df = grouped_df.merge(cls.material_prices, on='material', how='left')
        grouped_df['cost'] = grouped_df['price'] * grouped_df['volume']
        return grouped_df

    @classmethod
    def get_element_costs(cls):
        if cls.df.empty:
            return pd.DataFrame()
        
        merged_df = cls.df.merge(cls.material_prices, on='material', how='left')
        merged_df['cost'] = merged_df['price'] * merged_df['volume']
        grouped_df = merged_df.groupby('element', as_index=False).agg({'cost': 'sum', 'volume': 'sum'})
        return grouped_df

    @classmethod
    def get_data(cls, type: str, type_attr: str):
        if type == "material":
            data = cls.get_material_costs()
        elif type == "element":
            data = cls.get_element_costs()
        else:
            raise ValueError('Invalid type. Must be "material" or "element".')

        if type_attr not in data.columns:
            raise ValueError(f'Invalid type attribute. Must be one of {list(data.columns)}.')

        if data.empty or data[type_attr].sum() == 0:
            raise ValueError('No available data or the sum of the data is zero.')
        
        if type_attr == 'price':
            type_attr = 'cost'

        return data[['material' if type == 'material' else 'element', type_attr]]

    @classmethod
    def can_create_pie_chart(cls, type: str, type_attr: str):
        try:
            data = cls.get_data(type, type_attr)
            if not data.empty and data.iloc[:, 1].sum() > 0:
                return True
        except ValueError:
            return False
        return False

    @classmethod
    def get_pie_chart_error_message(cls, type: str, type_attr: str):
        if type == "material":
            data = cls.get_material_costs()
        elif type == "element":
            data = cls.get_element_costs()
        else:
            return 'Nieprawidłowy typ. Musi być "material" lub "element".'

        if data.empty:
            return "Nie ma danych"
        
        if type_attr not in data.columns:
            return f'Nieprawidłowy atrybut typu. Musi być jednym z {list(data.columns)}.'

        if type_attr == 'cost' and data['cost'].sum() == 0:
            return "Wszystkie wartości cenowe wynoszą 0"

        return ""

    @classmethod
    def get_total_cost(cls):
        material_costs = cls.get_material_costs()
        return material_costs['cost'].sum()

if __name__ == '__main__':
    print('test ifc_data.py')
    ifc_data = IfcData()
    ifc_data.load('example_file.ifc')
    # print(ifc_data.get_element_costs())
    # print(ifc_data.get_material_costs())
    # IfcData.load('example_file.ifc')
    # IfcData.update_material_price('Concrete', 10)
    # print(IfcData.get_material_costs())
    # print(ifc_data.get_element_costs())

