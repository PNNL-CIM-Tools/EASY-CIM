from __future__ import annotations
import logging
import enum



_log = logging.getLogger(__name__)

def get_data(obj:object, attribute_list:list[str], data:dict = {}) -> dict:
    cim_class = obj.__class__
    if not data:
        data = {}
    for attribute in attribute_list:
        if attribute in cim_class.__dataclass_fields__:
            value = getattr(obj, attribute)
            if type(value.__class__) is enum.EnumMeta:
                value = value.value
            elif value is None:
                value = 'None'
            data[attribute] = value
        else:
            _log.warning(f'{attribute} not in CIM profile')
    return data

