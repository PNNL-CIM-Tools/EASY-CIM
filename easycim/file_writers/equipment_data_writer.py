import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Union, Any
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from cimgraph.models import GraphModel

_log = logging.getLogger(__name__)

class EquipmentDataWriter:
    """File writer for equipment data exports"""
    
    @staticmethod
    def write_json(data: Dict, file_path: Union[str, Path], 
                   indent: int = 2, ensure_ascii: bool = False) -> None:
        """Write equipment data to JSON file"""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
        
        _log.info(f"Equipment data written to {file_path}")
    
    @staticmethod
    def write_csv(data: Dict, file_path: Union[str, Path],
                  flatten_nested: bool = True) -> None:
        """Write equipment data to CSV file"""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not data:
            _log.warning("No data to write to CSV")
            return
        
        # Flatten data for CSV format
        flattened_data = []
        for equipment_id, equipment_data in data.items():
            if flatten_nested:
                flat_row = EquipmentDataWriter._flatten_dict(equipment_data)
                flat_row['equipment_id'] = equipment_id
                flattened_data.append(flat_row)
            else:
                equipment_data['equipment_id'] = equipment_id
                flattened_data.append(equipment_data)
        
        if flattened_data:
            fieldnames = set()
            for row in flattened_data:
                fieldnames.update(row.keys())
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
                writer.writeheader()
                writer.writerows(flattened_data)
            
            _log.info(f"Equipment data written to {file_path}")
    
    @staticmethod
    def _flatten_dict(data: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """Flatten nested dictionary for CSV export"""
        items = []
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            
            if isinstance(value, dict):
                items.extend(EquipmentDataWriter._flatten_dict(value, new_key, sep).items())
            elif isinstance(value, list):
                # Handle lists by creating indexed keys
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        items.extend(EquipmentDataWriter._flatten_dict(item, f"{new_key}_{i}", sep).items())
                    else:
                        items.append((f"{new_key}_{i}", str(item)))
            else:
                items.append((new_key, value))
        
        return dict(items)
    
    @staticmethod
    def write_excel(data: Dict, file_path: Union[str, Path],
                   sheet_name: str = 'Equipment Data') -> None:
        """Write equipment data to Excel file (requires openpyxl)"""
        try:
            import openpyxl
            from openpyxl import Workbook
        except ImportError:
            raise ImportError("openpyxl is required for Excel export. Install with: pip install openpyxl")
        
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Flatten data
        flattened_data = []
        for equipment_id, equipment_data in data.items():
            flat_row = EquipmentDataWriter._flatten_dict(equipment_data)
            flat_row['equipment_id'] = equipment_id
            flattened_data.append(flat_row)
        
        if not flattened_data:
            _log.warning("No data to write to Excel")
            return
        
        # Create workbook and worksheet
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name
        
        # Write headers
        headers = sorted(set().union(*(row.keys() for row in flattened_data)))
        ws.append(headers)
        
        # Write data rows
        for row_data in flattened_data:
            row = [row_data.get(header, '') for header in headers]
            ws.append(row)
        
        wb.save(file_path)
        _log.info(f"Equipment data written to {file_path}")

# # ===== CONVENIENCE FUNCTIONS =====

# def export_line_impedance_data(network: GraphModel, 
#                               output_file: Union[str, Path],
#                               format: str = 'json',
#                               shacl_shapes_file: str = None) -> None:
#     """Export line impedance data to file"""
    
#     line_data = get_impedance_data_per_line(network, shacl_shapes_file)
    
#     if format.lower() == 'json':
#         EquipmentDataWriter.write_json(line_data, output_file)
#     elif format.lower() == 'csv':
#         EquipmentDataWriter.write_csv(line_data, output_file)
#     elif format.lower() in ['xlsx', 'excel']:
#         EquipmentDataWriter.write_excel(line_data, output_file, 'Line Impedance Data')
#     else:
#         raise ValueError(f"Unsupported format: {format}")

# def export_all_equipment_data(network: GraphModel,
#                              output_dir: Union[str, Path],
#                              format: str = 'json',
#                              shacl_shapes_file: str = None) -> None:
#     """Export all equipment data to separate files"""
    
#     output_dir = Path(output_dir)
#     output_dir.mkdir(parents=True, exist_ok=True)
    
#     all_data = get_all_equipment_data(network, shacl_shapes_file=shacl_shapes_file)
    
#     for equipment_type, equipment_data in all_data.items():
#         output_file = output_dir / f"{equipment_type.lower()}_data.{format}"
        
#         if format.lower() == 'json':
#             EquipmentDataWriter.write_json(equipment_data, output_file)
#         elif format.lower() == 'csv':
#             EquipmentDataWriter.write_csv(equipment_data, output_file)
#         elif format.lower() in ['xlsx', 'excel']:
#             EquipmentDataWriter.write_excel(equipment_data, output_file, f'{equipment_type} Data')