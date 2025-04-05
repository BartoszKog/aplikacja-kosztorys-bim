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
        """
        Extract volume information from IFC element using different strategies.
        
        Args:
            element: IFC element from which to extract volume.
            
        Returns:
            Float value of volume if found, None otherwise.
        """
        # First check using the original simple method for backward compatibility
        psets = util_element.get_psets(element)
        for pset_name, pset in psets.items():
            if 'NetVolume' in pset:
                return pset['NetVolume']
        
        # Continue with additional checks if the simple method didn't find a volume
        for pset_name, pset in psets.items():
            # Look for different volume representation names in psets
            if 'Volume' in pset:
                return pset['Volume']
            if 'GrossVolume' in pset:
                return pset['GrossVolume']
            if 'TotalVolume' in pset:
                return pset['TotalVolume']
                
        # Check quantities for volume information
        quantities = util_element.get_quantities(element)
        for quantity_name, quantity in quantities.items():
            # Look for different volume representation names in quantities
            if 'NetVolume' in quantity:
                return quantity['NetVolume']
            if 'Volume' in quantity:
                return quantity['Volume']
            if 'GrossVolume' in quantity:
                return quantity['GrossVolume']
            
        # Try direct attribute access as a last resort
        try:
            if hasattr(element, 'Volume'):
                return element.Volume
        except:
            pass
            
        return None

    @classmethod
    def __get_material_name(cls, material):
        """
        Extract material name from various types of IFC material objects.
        
        Args:
            material: IFC material object
            
        Returns:
            String representing the material name.
            
        Raises:
            AttributeError: If material name cannot be extracted.
        """
        # Handle direct material with Name attribute
        if material.is_a('IfcMaterial'):
            return material.Name
            
        # Handle IfcMaterialLayerSet
        elif material.is_a('IfcMaterialLayerSet'):
            if hasattr(material, 'LayerSetName') and material.LayerSetName:
                return material.LayerSetName
            # Fallback to first layer's material name
            elif hasattr(material, 'MaterialLayers') and material.MaterialLayers:
                layers = list(material.MaterialLayers)
                if layers and hasattr(layers[0], 'Material') and layers[0].Material:
                    return layers[0].Material.Name
            raise AttributeError(f"Cannot extract name from {material.is_a()}")
                
        # Handle IfcMaterialLayerSetUsage
        elif material.is_a('IfcMaterialLayerSetUsage'):
            if hasattr(material, 'ForLayerSet') and material.ForLayerSet:
                return cls.__get_material_name(material.ForLayerSet)
            raise AttributeError(f"Cannot extract name from {material.is_a()}")
                
        # Handle IfcMaterialList
        elif material.is_a('IfcMaterialList'):
            if hasattr(material, 'Materials') and material.Materials:
                materials = list(material.Materials)
                if materials and hasattr(materials[0], 'Name'):
                    return materials[0].Name
            raise AttributeError(f"Cannot extract name from {material.is_a()}")
                
        # Handle IfcMaterialConstituentSet
        elif material.is_a('IfcMaterialConstituentSet'):
            if hasattr(material, 'Name') and material.Name:
                return material.Name
            elif hasattr(material, 'MaterialConstituents') and material.MaterialConstituents:
                constituents = list(material.MaterialConstituents)
                if constituents and hasattr(constituents[0], 'Material') and constituents[0].Material:
                    return constituents[0].Material.Name
            raise AttributeError(f"Cannot extract name from {material.is_a()}")
                
        # Fallback for any other material type
        elif hasattr(material, 'Name'):
            return material.Name
            
        # If no name could be found, throw an error
        raise AttributeError(f"Material of type {material.is_a()} has no extractable name")

    @classmethod
    def __update_material_prices(cls, material: str):
        if material not in list(cls.material_prices['material']):
            cls.material_prices = pd.concat([
                cls.material_prices,
                pd.DataFrame([{'material': material, 'price': 0}])
            ], ignore_index=True)

    @classmethod
    def update_material_price(cls, material: str, price: float):
        cls.__update_material_prices(material)
        cls.material_prices.loc[cls.material_prices['material'] == material, 'price'] = price

    @classmethod
    def __update_df(cls):
        """
        Update dataframe with elements, materials and volumes from the IFC model.
        
        This method processes all material associations in the IFC model,
        extracts material names and element volumes, and updates the dataframe.
        
        Raises:
            AssertionError: If IFC file is not loaded.
        """
        assert cls.model is not None, 'IFC file not loaded'
        processed_elements = set()  # Track processed elements to avoid duplicates
        
        # Process material associations
        for associates_material in cls.model.by_type('IfcRelAssociatesMaterial'):
            material = associates_material.RelatingMaterial
            
            try:
                # Extract material name using robust helper method
                material_name = cls.__get_material_name(material)
                
                for element in associates_material.RelatedObjects:
                    element_id = element.id()
                    if element_id in processed_elements:
                        continue
                        
                    volume = cls.__get_net_volume_from_element(element)
                    if volume is None:
                        continue
                        
                    cls.df = pd.concat([
                        cls.df,
                        pd.DataFrame([{
                            'element': element.is_a(),
                            'material': material_name,
                            'volume': volume
                        }])
                    ], ignore_index=True)
                    cls.__update_material_prices(material_name)
                    processed_elements.add(element_id)
                    
            except AttributeError:
                # Skip this material association if name cannot be extracted
                continue
        
        # Special handling for structural elements (IfcBeam, IfcColumn) that might have been skipped
        for element_type in ['IfcBeam', 'IfcColumn', 'IfcSlab', 'IfcWall', 'IfcStairFlight']:
            for element in cls.model.by_type(element_type):
                element_id = element.id()
                if element_id in processed_elements:
                    continue
                    
                # Check if element has an assigned volume
                volume = cls.__get_net_volume_from_element(element)
                if volume is None:
                    continue
                
                # Check if material can be found for the element
                material_name = None
                
                # Try to find material in relationships
                for rel in cls.model.by_type('IfcRelAssociatesMaterial'):
                    if element.id() in [obj.id() for obj in rel.RelatedObjects]:
                        try:
                            material_name = cls.__get_material_name(rel.RelatingMaterial)
                            break
                        except AttributeError:
                            continue
                
                # If no material was found, use default for structural element
                if material_name is None:
                    if element_type in ['IfcBeam', 'IfcColumn']:
                        material_name = 'Structural steel - S235'  # Default material for beams and columns
                    else:
                        material_name = f'Default material for {element_type}'
                
                cls.df = pd.concat([
                    cls.df,
                    pd.DataFrame([{
                        'element': element.is_a(),
                        'material': material_name,
                        'volume': volume
                    }])
                ], ignore_index=True)
                cls.__update_material_prices(material_name)
                processed_elements.add(element_id)

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
    print('=== IFC DATA PROCESSING TEST ===')
    
    # Test 1: Process problematic file 'AC20-Institute-Var-2.ifc'
    print('\nTest 1: Processing problematic file AC20-Institute-Var-2.ifc')
    try:
        ifc_data = IfcData()
        ifc_data.load('AC20-Institute-Var-2.ifc')
        material_costs = ifc_data.get_material_costs()
        element_costs = ifc_data.get_element_costs()
        
        print(f"Success! Processed AC20-Institute-Var-2.ifc")
        print(f"Found {len(material_costs)} materials and {len(element_costs)} element types")
        
        if not material_costs.empty:
            print(f"Sample materials: {material_costs['material'].head(3).tolist()}")
            print(f"Total material volume: {material_costs['volume'].sum():.2f}")
        
    except Exception as e:
        print(f"Error processing AC20-Institute-Var-2.ifc: {str(e)}")
    
    # Test 2: Process previously working file 'example_file.ifc'
    print('\nTest 2: Processing previously working file example_file.ifc')
    try:
        ifc_data = IfcData()
        ifc_data.load('example_file.ifc')
        material_costs = ifc_data.get_material_costs()
        element_costs = ifc_data.get_element_costs()
        
        print(f"Success! Processed example_file.ifc")
        print(f"Found {len(material_costs)} materials and {len(element_costs)} element types")
        
        if not material_costs.empty:
            print(f"Sample materials: {material_costs['material'].head(3).tolist()}")
            print(f"Total material volume: {material_costs['volume'].sum():.2f}")
        
        # Test material price update functionality
        if not material_costs.empty and len(material_costs) > 0:
            test_material = material_costs['material'].iloc[0]
            test_price = 100.0
            print(f"\nTesting material price update for '{test_material}'")
            
            ifc_data.update_material_price(test_material, test_price)
            updated_costs = ifc_data.get_material_costs()
            updated_row = updated_costs[updated_costs['material'] == test_material]
            
            if not updated_row.empty:
                print(f"Material: {test_material}")
                print(f"Price: {updated_row['price'].iloc[0]}")
                print(f"Volume: {updated_row['volume'].iloc[0]:.2f}")
                print(f"Cost: {updated_row['cost'].iloc[0]:.2f}")
        
    except Exception as e:
        print(f"Error processing example_file.ifc: {str(e)}")
    
    print('\n=== TEST COMPLETED ===')

