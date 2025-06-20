import enum
import logging
from dataclasses import is_dataclass

from cimgraph.databases import get_cim_profile
from cimgraph.data_profile.identity import Identity

_log = logging.getLogger(__name__)


INDENT = '    '

def short_attr_mermaid(obj: object, attr: str, num_indent: int = 1) -> str:
    """
    Generate a mermaid short representation of an attribute.

    Args:
        obj (object): The object containing the attribute.
        attr (str): The attribute name.
        num_indent (int, optional): Number of indentations. Defaults to 1.

    Returns:
        str: The mermaid representation of the attribute.
    """
    mermaid = ''
    edge = getattr(obj, attr)
    if len(attr) > 22:
        mermaid += f'\n{INDENT*(num_indent)}{attr[:22]}\n'
        mermaid += f'{INDENT*(num_indent)}{attr[22:]}:'
    else:
        mermaid += '\n' + INDENT*(num_indent) + f'{attr}: '
    if len(str(edge)) > 22:
        mermaid += f'{edge[:22]}\n'
        mermaid += f'{edge[22:]}'
    else:
        mermaid += f'{edge}'
    return mermaid

def short_uri_mermaid(obj: object, num_indent: int = 1) -> str:
    """
    Generate a mermaid short representation of an object's URI.

    Args:
        obj (object): The object.
        num_indent (int, optional): Number of indentations. Defaults to 1.

    Returns:
        str: The mermaid representation of the object's URI.
    """
    mermaid = ''
    obj_class = obj.__class__.__name__
    short_uri = obj.uri().split('-')[0]
    if len(obj_class) > 22:
        mermaid += INDENT*(num_indent) + short_uri + f'(**{obj_class[:22]}**\n'
        mermaid += INDENT*(num_indent+1) + f'**{obj_class[22:]}**'
    else:
        mermaid += INDENT*(num_indent) + short_uri + f'(**{obj_class}**'
    if 'name' in obj.__dataclass_fields__:
        mermaid += short_attr_mermaid(obj, 'name', num_indent+1)
    else:
        mermaid += INDENT*(num_indent+2) + obj.uri() + '\n'
    mermaid += ')\n'
    return mermaid


    """
    Generate a mermaid mindmap of an object.

    Args:
        obj (object): The object to represent.

    Returns:
        str: The mermaid mindmap representation of the object.
    """
    mermaid = 'mindmap\n'
    # Build starting node as round circle with all attributes that are not None
    mermaid += short_uri_mermaid(obj).replace('(','((')[:-2]
    for attribute in obj.__dataclass_fields__:
        edge = getattr(obj, attribute)
        if type(edge) in [str, bool, float, int] and attribute not in ['name','mRID']:
            mermaid += short_attr_mermaid(obj, attribute, num_indent=2)
    mermaid += '))\n'

    # Expand and build all connected objects
    for attribute in obj.__dataclass_fields__:
        edge = getattr(obj, attribute)
        if is_dataclass(edge) and edge is not None:
            if len(attribute) > 22:
                mermaid += f'\n{INDENT*2}[{attribute[:22]}\n'
                mermaid += f'{INDENT*2}{attribute[22:]}]\n'
            else:
                mermaid += INDENT*2 + f'[{attribute}]\n'
            mermaid += short_uri_mermaid(edge, num_indent=3)

        elif type(edge) == list and edge != []:
            if len(attribute) > 22:
                mermaid += f'\n{INDENT*2}[{attribute[:22]}\n'
                mermaid += f'{INDENT*2}{attribute[22:]}]\n'
            else:
                mermaid += INDENT*2 + f'["{attribute}"]\n'
            for item in edge:
                if is_dataclass(item):
                    mermaid += short_uri_mermaid(item, num_indent=3)

    return mermaid

def class_schema(cim_class: type, show_attributes: bool = True, show_inherited: bool = True) -> str:
    """
    
    """
    # Get list of all classes from which cim_class inherits
    parent_classes = list(cim_class.__mro__)
    parent_classes.pop(len(parent_classes) - 1)
    schema = {}

    if type(cim_class) is not enum.EnumMeta: # Parse classes that are not enumerations
        class_name = cim_class.__name__
        schema['@type'] = class_name
        if show_attributes:
            # Iterate through all attributes of cim_class
            for attribute in cim_class.__annotations__.keys():
                attr = cim_class.__dataclass_fields__[attribute]
                attr_type = str(attr.type)
                try:
                    if 'Attribute' in attr.metadata['type']:
                        edge = attr_type.split('[')[1].split(']')[0]
                        schema[attribute] = edge
                    elif 'enumeration' in attr.metadata['type']:
                        edge = attr_type.split('[')[1].split(']')[0]
                        schema[attribute] = edge
                except:
                    pass

            if show_inherited:
                for parent in parent_classes:
                    if len(parent.__annotations__.keys()) > 0 and parent.__name__ != cim_class.__name__:
                        for attribute in parent.__annotations__.keys():
                            attr = parent.__dataclass_fields__[attribute]
                            attr_type = str(attr.type)
                            try:
                                if 'Attribute' in attr.metadata['type'] or 'enumeration' in attr.metadata['type']:
                                    edge = attr_type.split('[')[1].split(']')[0]
                                    schema[attribute] = edge

                            except:
                                pass



    return schema

def class_assc_schema(cim_class: type, association: str) -> str:
    """
    Generate a mermaid class association diagram.

    Args:
        cim_class (type): The CIM class to represent.
        association (str): The association name.

    Returns:
        str: The mermaid class association diagram.
    """
    cim_profile, cim = get_cim_profile()

    if '__subclasses__' in association:
        edge_class = eval(f'cim_class.{association}')
        attr_type = 'inheritance'
    else:
        attr = cim_class.__dataclass_fields__[association]
        attr_type = str(attr.type)

        # try:
            # if 'Association' in attr.metadata['type'] or 'Of Aggregate' in attr.metadata['type']:
        edge = attr_type.split('[')[1].split(']')[0].replace('|', 'or')
        edge_class = getattr(cim, edge)
    if 'list' in attr_type:
        schema = [class_schema(edge_class)]
        # mermaid += f'{INDENT}{cim_class.__name__} --> "0..*" {edge} : {association} \n'
    else:
        schema = class_schema(edge_class)
                # mermaid += f'{INDENT}{cim_class.__name__} --> "0..1" {edge} : {association} \n'
        # elif 'Aggregate Of' in attr.metadata['type']:
        #     edge = attr_type.split('[')[1].split(']')[0].replace('|', 'or')
        #     if 'list' in attr_type:
        #         mermaid += f'{INDENT}{cim_class.__name__} --o "0..*" {edge} : {association} \n'
        #     else:
        #         mermaid += f'{INDENT}{cim_class.__name__} --o "0..1" {edge} : {association} \n'
    # except:
    #     pass
    return schema

def class_all_assc_mermaid(cim_class: type, show_inherited: bool = False) -> str:
    """
    Generate a mermaid diagram of all class associations.

    Args:
        cim_class (type): The CIM class to represent.
        show_inherited (bool, optional): Whether to show inherited associations. Defaults to False.

    Returns:
        str: The mermaid diagram of all class associations.
    """
    parent_classes = list(cim_class.__mro__)
    parent_classes.pop(len(parent_classes) - 1)
    mermaid = ''

    if type(cim_class) is not enum.EnumMeta and len(parent_classes) > 1:
        mermaid += INDENT + f'{parent_classes[1].__name__} <|-- {cim_class.__name__} : inherits from\n'

        for attribute in cim_class.__annotations__.keys():
            mermaid += class_assc_mermaid(cim_class, attribute)

        if show_inherited:
            for parent_class in parent_classes:
                if len(parent_class.__annotations__.keys()) > 0 and parent_class.__name__ != cim_class.__name__:
                    for attribute in parent_class.__annotations__.keys():
                        mermaid += class_assc_mermaid(cim_class, attribute)

    return mermaid

def get_schema(root: object | type | list, show_attributes: bool = True, show_inherited: bool = True,
                theme: str = 'neutral', layout: str = 'dagre') -> str:
    """
    Generate a mermaid representation of provided root object or class.

    Args:
        root (object | type | list): The root object or class to represent.
        show_attributes (bool, optional): Whether to show attributes. Defaults to True.
        show_inherited (bool, optional): Whether to show inherited attributes. Defaults to False.
        theme (str, optional): The theme for mermaid diagram. Defaults to 'neutral'.
        layout (str, optional): The layout for mermaid diagram. Defaults to 'dagre'.

    Returns:
        str: The mermaid diagram representation.
    """


    if is_dataclass(root):
        schema = class_schema(root, show_attributes, show_inherited)
        # mermaid += class_all_assc_mermaid(root, show_inherited)
    # elif type(root) == list:
    #     if set(map(type, root)) == {type} or set(map(type, root)) == {enum.EnumMeta, type}:
    #         # mermaid = '%%{init: {"theme":"' + str(theme) + "'}}%%\n"
    #         # mermaid += 'classDiagram\n'
    #         schema = {}
    #         for value in root:
    #             # schema = schema | class_json(value, show_attributes, show_inherited)
    #             for attr in value.__annotations__:
    #                 try:
    #                     next_str = value.__annotations__[attr]
    #                     next_class_name = next_str.split('[')[1].split(']')[0]
    #                     # next_class = getattr(value.__module__, next_class_name)
    #                     next_class = eval(f'{value.__module__}.{next_class_name}')
    #                     if next_class in root:
    #                         mermaid += class_assc_mermaid(value, attr)
    #                 except:
    #                     pass
    #             parent_classes = list(value.__mro__)
    #             if len(parent_classes) > 1:
    #                 if parent_classes[1] in root:
    #                     mermaid += INDENT + f'{parent_classes[1].__name__} <|-- {value.__name__} : inherits from\n'

        # if set(map(isinstance, root, [Identity] * len(root))) == {True}:
        #     mermaid = ''
        #     for value in root:
        #         mermaid += object_mermaid(value)

    return schema



def add_class_path_schema(root: type, path: str | list[str], schema: str,
                           show_attributes: bool = True, show_inherited: bool = False) -> str:
    """
    Add a class path representation to an existing mermaid diagram.

    Args:
        root (type): The root class.
        path (str | list[str]): The attribute path.
        mermaid (str): The initial mermaid diagram.
        show_attributes (bool, optional): Whether to show attributes. Defaults to True.
        show_inherited (bool, optional): Whether to show inherited attributes. Defaults to False.

    Returns:
        str: The updated mermaid diagram with the class path representation.
    """
    cim_profile, cim = get_cim_profile()
    edge = root
    
    if type(path) is list:
        pass
    elif type(path) is str:
        path = path.split('.')
    for attr in path:
        class_name = edge.__name__

        if '__subclasses__' in attr:
            next_class = eval(f'edge.{attr}')
        else:
            schema[attr] = class_assc_schema(edge, attr)

            next_str = edge.__dataclass_fields__[attr]
            # next_class = getattr(cim, next_str)
            next_class_name = next_str.type.split('[')[1].split(']')[0]
            
            next_class = getattr(cim, next_class_name)
           
        edge = next_class
    return schema

def get_schema_path(root: object | type, path: str | list[str],
                     direction: str = 'LR', theme: str = 'neutral',
                     show_attributes: bool = True, show_inherited: bool = False) -> str:
    """
    Generate a mermaid diagram of a specified path starting from a root object or class.
    The path is a cimgraph traversal (e.g. '.Terminals[0].ConnectivityNode') or
    a list with UML association names separated by commas (e.g. ['Terminals','[0]'])

    Args:
        root (object | type): The root object or class.
        path (str, list[str]): The attribute path
        direction (str, optional): The direction of the diagram. Defaults to 'LR'.
        theme (str, optional): The theme for the diagram. Defaults to 'neutral'.
        show_attributes (bool, optional): Whether to show attributes. Defaults to True.
        show_inherited (bool, optional): Whether to show inherited attributes. Defaults to False.

    Returns:
        str: The mermaid diagram representation of the specified path.
    """


    if is_dataclass(root):

        schema = class_schema(root, show_inherited)
        schema = add_class_path_schema(root, path, schema, show_attributes, show_inherited)
    return schema

def add_schema_path(root: object | type, path: str | list[str], mermaid: str,
                     show_attributes: bool = True, show_inherited: bool = False) -> str:
    """
    Add a mermaid path representation to an existing diagram.

    Args:
        root (object | type): The root object or class.
        path (str, list[str]): The attribute path.
        mermaid (str): The initial mermaid diagram.
        show_attributes (bool, optional): Whether to show attributes. Defaults to True.
        show_inherited (bool, optional): Whether to show inherited attributes. Defaults to False.

    Returns:
        str: The updated mermaid diagram with the path representation.
    """
    
    if is_dataclass(root):
        mermaid = add_class_path_schema(root, path, mermaid, show_attributes, show_inherited)
    return mermaid
