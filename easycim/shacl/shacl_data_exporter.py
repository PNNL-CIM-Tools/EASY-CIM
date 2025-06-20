from __future__ import annotations
import importlib
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any
from cimgraph.models import GraphModel
from cimgraph.shacl import SHACLCatalogProcessor

_log = logging.getLogger(__name__)

@dataclass
class SHACLDataExporter:
    """SHACL-based data exporter that replaces ReducedDataProfile"""
    
    shacl_shapes_file: str
    cim_module: object
    processor: SHACLCatalogProcessor = field(init=False)
    
    def __post_init__(self):
        self.processor = SHACLCatalogProcessor(self.shacl_shapes_file, self.cim_module)
    
    def export_object_data(self, obj: Any, shape_name: str = None) -> dict:
        """Export single object data using SHACL shape"""
        if shape_name is None:
            shape_name = f"{obj.__class__.__name__}Export"
        
        if shape_name not in self.processor.catalog_shapes:
            _log.warning(f"No export shape found for {obj.__class__.__name__}")
            return self._fallback_export(obj)
        
        catalog_shape = self.processor.catalog_shapes[shape_name]
        # Create a minimal GraphModel for the processor
        temp_graph = type('TempGraph', (), {'list_by_class': lambda cls: []})()
        
        return self.processor._serialize_object(obj, catalog_shape, temp_graph)
    
    def _fallback_export(self, obj: Any) -> dict:
        """Fallback export for objects without SHACL shapes"""
        result = {"@type": obj.__class__.__name__}
        
        if hasattr(obj, 'mRID'):
            result['mRID'] = str(obj.mRID)
        if hasattr(obj, 'identifier'):
            result['mRID'] = str(obj.identifier)
        if hasattr(obj, 'name') and getattr(obj, 'name'):
            result['name'] = getattr(obj, 'name')
            
        return result