from __future__ import annotations
import logging
import enum



_log = logging.getLogger(__name__)

def get_data(obj:object, attribute_list:list[str], data:dict = {}) -> dict:
    """Data iterator to extract all values from a cimgraph object instance.
    By default, creates a new dictionary with attributes defined in reduced
    data profile. For classes with deep inheritance trees, the data dictionary
    generated from the parent class can be passed in as an optional arguement.

    :param obj: CIM object instance
    :type obj: object
    :param attribute_list: List of attributes from reduced data profile
    :type attribute_list: list[str]
    :param data: Data structure of parent class, defaults to {}
    :type data: dict, optional
    :return: Dictionary of CIM object data
    :rtype: dict
    """    
    cim_class = obj.__class__
    if not data:
        data = {}
    try:
        for attribute in attribute_list:
            if attribute in cim_class.__dataclass_fields__:
                value = getattr(obj, attribute)
                if type(value.__class__) is enum.EnumMeta:
                    value = value.value
                elif value is None:
                    value = 'None'
                data[attribute] = value
            else:
                _log.info(f'{attribute} not in CIM profile')
    except:
        _log.warning(f'unable to parse {obj}')
    return data

