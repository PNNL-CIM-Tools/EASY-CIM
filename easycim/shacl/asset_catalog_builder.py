from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field

from cimgraph.models import GraphModel
from cimgraph.databases import get_cim_profile
from easycim.shacl.shacl_data_exporter import SHACLDataExporter
from easycim.file_writers import EquipmentDataWriter

_log = logging.getLogger(__name__)

@dataclass
class AssetCatalogBuilder:
    """SHACL-driven asset catalog builder for CIM-Builder integration"""
    
    network: GraphModel
    shacl_shapes_file: str = None
    catalog_output_dir: Path = field(default_factory=lambda: Path('./asset_catalogs'))
    cim_profile: str = field(init=False)
    cim_module: object = field(init=False)
    exporter: SHACLDataExporter = field(init=False)
    
    def __post_init__(self):
        self.cim_profile, self.cim_module = get_cim_profile()
        
        if self.shacl_shapes_file is None:
            self.shacl_shapes_file = self._get_default_catalog_shapes_file()
        
        self.exporter = SHACLDataExporter(self.shacl_shapes_file, self.cim_module)
        self.catalog_output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_equipment_catalogs(self, equipment_types: List[str] = None) -> Dict[str, str]:
        """
        Create catalog files for all specified equipment types
        
        :param equipment_types: List of CIM class names to create catalogs for
        :return: Dictionary mapping equipment type to catalog file path
        """
        
        if equipment_types is None:
            equipment_types = [
                'PowerTransformer', 'ACLineSegment', 'EnergyConsumer',
                'PowerElectronicsConnection', 'LinearShuntCompensator',
                'EnergySource', 'Switch', 'Breaker'
            ]
        
        catalog_files = {}
        
        for equipment_type in equipment_types:
            try:
                catalog_file = self.create_equipment_type_catalog(equipment_type)
                catalog_files[equipment_type] = str(catalog_file)
                _log.info(f"Created catalog for {equipment_type}: {catalog_file}")
            except Exception as e:
                _log.error(f"Failed to create catalog for {equipment_type}: {e}")
        
        return catalog_files
    
    def create_equipment_type_catalog(self, equipment_type: str) -> Path:
        """
        Create catalog file for a specific equipment type
        
        :param equipment_type: CIM class name
        :return: Path to created catalog file
        """
        
        if not hasattr(self.cim_module, equipment_type):
            raise ValueError(f"Equipment type {equipment_type} not found in CIM profile")
        
        cim_class = getattr(self.cim_module, equipment_type)
        
        # Get all equipment of this type
        equipment_list = self.network.list_by_class(cim_class)
        
        if not equipment_list:
            _log.warning(f"No equipment of type {equipment_type} found in network")
            return None
        
        # Create catalog entries
        catalog_entries = []
        shape_name = f"{equipment_type}Export"
        
        # Fallback to polymorphic shapes if specific shape not available
        if shape_name not in self.exporter.processor.catalog_shapes:
            fallback_shapes = {
                'PowerTransformer': 'PowerTransformerExport',
                'ACLineSegment': 'ACLineSegmentExport', 
                'EnergyConsumer': 'LoadPolymorphicExport',
                'PowerElectronicsConnection': 'PowerElectronicsConnectionExport',
                'EnergySource': 'EnergySourceExport'
            }
            shape_name = fallback_shapes.get(equipment_type, shape_name)
        
        for equipment in equipment_list:
            try:
                catalog_entry = self.exporter.export_object_data(equipment, shape_name)
                
                # Post-process for CIM-Builder compatibility
                catalog_entry = self._prepare_for_cim_builder(catalog_entry, equipment_type)
                catalog_entries.append(catalog_entry)
                
            except Exception as e:
                _log.warning(f"Failed to export {equipment.identifier}: {e}")
        
        # Group similar equipment
        grouped_catalogs = self._group_similar_equipment(catalog_entries, equipment_type)
        
        # Write catalog files
        catalog_files = []
        for group_name, group_entries in grouped_catalogs.items():
            catalog_file = self._write_catalog_file(equipment_type, group_name, group_entries)
            catalog_files.append(catalog_file)
        
        return catalog_files[0] if catalog_files else None
    
    def _prepare_for_cim_builder(self, catalog_entry: Dict, equipment_type: str) -> Dict:
        """
        Prepare catalog entry for CIM-Builder compatibility
        
        This method ensures the catalog format matches what CIM-Builder expects
        """
        
        # Remove instance-specific identifiers that should be generated fresh
        if 'mRID' in catalog_entry:
            del catalog_entry['mRID']
        
        # Convert certain fields to strings for CIM-Builder parsing
        string_fields = ['endNumber', 'sequenceNumber', 'phaseAngleClock']
        self._convert_to_strings(catalog_entry, string_fields)
        
        # Handle nested objects
        if equipment_type == 'PowerTransformer':
            self._prepare_transformer_catalog(catalog_entry)
        elif equipment_type == 'ACLineSegment':
            self._prepare_line_catalog(catalog_entry)
        elif equipment_type == 'PowerElectronicsConnection':
            self._prepare_inverter_catalog(catalog_entry)
        
        return catalog_entry
    
    def _prepare_transformer_catalog(self, catalog_entry: Dict) -> None:
        """Prepare transformer catalog for CIM-Builder"""
        
        # Remove mRIDs from transformer ends
        for end in catalog_entry.get('PowerTransformerEnd', []):
            if 'mRID' in end:
                del end['mRID']
            if 'name' in end:
                del end['name']  # Will be generated based on transformer name
            
            # Ensure grounded is string
            if 'grounded' in end:
                end['grounded'] = str(end['grounded']).lower()
        
        # Sort ends by endNumber
        if 'PowerTransformerEnd' in catalog_entry:
            catalog_entry['PowerTransformerEnd'].sort(
                key=lambda x: int(x.get('endNumber', 0))
            )
    
    def _prepare_line_catalog(self, catalog_entry: Dict) -> None:
        """Prepare line catalog for CIM-Builder"""
        
        # Remove phase-specific data (will be set by CIM-Builder)
        if 'ACLineSegmentPhases' in catalog_entry:
            del catalog_entry['ACLineSegmentPhases']
        
        # Keep impedance characteristics
        impedance_fields = ['r', 'x', 'bch', 'r0', 'x0', 'b0ch', 'length']
        for field in impedance_fields:
            if field in catalog_entry and catalog_entry[field] is not None:
                catalog_entry[field] = str(catalog_entry[field])
    
    def _prepare_inverter_catalog(self, catalog_entry: Dict) -> None:
        """Prepare inverter catalog for CIM-Builder"""
        
        # Remove phases (will be set by CIM-Builder)
        if 'phases' in catalog_entry:
            del catalog_entry['phases']
        
        # Clean up power electronics units
        for unit in catalog_entry.get('PowerElectronicsUnit', []):
            if 'mRID' in unit:
                del unit['mRID']
            if 'name' in unit:
                del unit['name']
    
    def _convert_to_strings(self, data: Dict, string_fields: List[str]) -> None:
        """Recursively convert specified fields to strings"""
        
        for key, value in data.items():
            if key in string_fields and value is not None:
                data[key] = str(value)
            elif isinstance(value, dict):
                self._convert_to_strings(value, string_fields)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self._convert_to_strings(item, string_fields)
    
    def _group_similar_equipment(self, catalog_entries: List[Dict], 
                                equipment_type: str) -> Dict[str, List[Dict]]:
        """
        Group similar equipment into catalog templates
        
        This creates reusable templates by grouping equipment with similar characteristics
        """
        
        if equipment_type == 'PowerTransformer':
            return self._group_transformers(catalog_entries)
        elif equipment_type == 'ACLineSegment':
            return self._group_lines(catalog_entries)
        elif equipment_type == 'PowerElectronicsConnection':
            return self._group_inverters(catalog_entries)
        else:
            # Default grouping by rated characteristics
            return self._group_by_ratings(catalog_entries, equipment_type)
    
    def _group_transformers(self, transformers: List[Dict]) -> Dict[str, List[Dict]]:
        """Group transformers by voltage levels and vector group"""
        
        groups = {}
        
        for xfmr in transformers:
            # Get voltage levels
            voltages = []
            for end in xfmr.get('PowerTransformerEnd', []):
                rated_u = end.get('ratedU')
                if rated_u:
                    voltages.append(int(float(rated_u)))
            
            voltages.sort(reverse=True)
            vector_group = xfmr.get('vectorGroup', 'Unknown')
            
            if len(voltages) >= 2:
                group_name = f"{voltages[0]}_{voltages[1]}_{vector_group}"
            else:
                group_name = f"single_voltage_{vector_group}"
            
            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append(xfmr)
        
        # Return representative from each group
        return {name: [group[0]] for name, group in groups.items()}
    
    def _group_lines(self, lines: List[Dict]) -> Dict[str, List[Dict]]:
        """Group lines by impedance characteristics"""
        
        groups = {}
        
        for line in lines:
            # Create signature based on per-unit impedance
            r = float(line.get('r', 0) or 0)
            x = float(line.get('x', 0) or 0)
            
            # Round to create groups
            r_rounded = round(r, 4)
            x_rounded = round(x, 4)
            
            group_name = f"r{r_rounded}_x{x_rounded}"
            
            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append(line)
        
        return {name: [group[0]] for name, group in groups.items()}
    
    def _group_inverters(self, inverters: List[Dict]) -> Dict[str, List[Dict]]:
        """Group inverters by technology and rating"""
        
        groups = {}
        
        for inverter in inverters:
            # Determine technology from units
            technology = 'generic'
            units = inverter.get('PowerElectronicsUnit', [])
            
            for unit in units:
                unit_class = unit.get('__class__', '')
                if 'Battery' in unit_class:
                    technology = 'battery'
                    break
                elif 'PhotoVoltaic' in unit_class or 'Solar' in unit_class:
                    technology = 'solar'
                    break
                elif 'Wind' in unit_class:
                    technology = 'wind'
                    break
            
            # Get rating
            rated_s = inverter.get('ratedS')
            if rated_s:
                rating_kva = int(float(rated_s) / 1000)
                group_name = f"{technology}_{rating_kva}kva"
            else:
                group_name = f"{technology}_unknown_rating"
            
            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append(inverter)
        
        return {name: [group[0]] for name, group in groups.items()}
    
    def _group_by_ratings(self, equipment: List[Dict], equipment_type: str) -> Dict[str, List[Dict]]:
        """Default grouping by rated values"""
        
        groups = {}
        
        for item in equipment:
            # Find rating fields
            rating_keys = ['ratedS', 'ratedU', 'ratedCurrent', 'customerCount']
            signature = equipment_type
            
            for key in rating_keys:
                if key in item and item[key] is not None:
                    value = float(item[key])
                    signature += f"_{key}{int(value)}"
            
            if signature not in groups:
                groups[signature] = []
            groups[signature].append(item)
        
        return {name: [group[0]] for name, group in groups.items()}
    
    def _write_catalog_file(self, equipment_type: str, group_name: str, 
                           catalog_entries: List[Dict]) -> Path:
        """Write catalog file for CIM-Builder consumption"""
        
        # Use the first entry as the template
        template_entry = catalog_entries[0]
        
        # Wrap in catalog structure
        catalog_data = {
            "catalog": template_entry
        }
        
        # Create filename
        filename = f"{equipment_type.lower()}_{group_name}.json"
        catalog_file = self.catalog_output_dir / filename
        
        # Write file
        with open(catalog_file, 'w', encoding='utf-8') as f:
            json.dump(catalog_data, f, indent=4, ensure_ascii=False)
        
        return catalog_file
    
    def _get_default_catalog_shapes_file(self) -> str:
        """Get default SHACL shapes file for catalog export"""
        import os
        package_dir = os.path.dirname(__file__)
        return os.path.join(package_dir, 'shapes', 'catalog_export_shapes.ttl')
    
    # ===== CONVENIENCE METHODS =====
    
    def create_transformer_catalogs(self) -> Dict[str, str]:
        """Create transformer catalog templates"""
        return {'PowerTransformer': self.create_equipment_type_catalog('PowerTransformer')}
    
    def create_line_catalogs(self) -> Dict[str, str]:
        """Create line catalog templates"""
        return {'ACLineSegment': self.create_equipment_type_catalog('ACLineSegment')}
    
    def create_inverter_catalogs(self) -> Dict[str, str]:
        """Create inverter catalog templates"""
        return {'PowerElectronicsConnection': self.create_equipment_type_catalog('PowerElectronicsConnection')}
    
    def create_load_catalogs(self) -> Dict[str, str]:
        """Create load catalog templates"""
        return {'EnergyConsumer': self.create_equipment_type_catalog('EnergyConsumer')}
    
    def list_available_catalogs(self) -> List[str]:
        """List all available catalog files"""
        return [f.name for f in self.catalog_output_dir.glob('*.json')]
    
    def get_catalog_summary(self) -> Dict:
        """Get summary of created catalogs"""
        
        catalog_files = list(self.catalog_output_dir.glob('*.json'))
        
        summary = {
            'total_catalogs': len(catalog_files),
            'by_equipment_type': {},
            'catalog_files': []
        }
        
        for catalog_file in catalog_files:
            try:
                with open(catalog_file, 'r') as f:
                    catalog_data = json.load(f)
                
                equipment_type = catalog_data['catalog'].get('@type', 'Unknown')
                
                summary['by_equipment_type'][equipment_type] = summary['by_equipment_type'].get(equipment_type, 0) + 1
                summary['catalog_files'].append({
                    'file': catalog_file.name,
                    'type': equipment_type,
                    'path': str(catalog_file)
                })
                
            except Exception as e:
                _log.warning(f"Could not read catalog file {catalog_file}: {e}")
        
        return summary