from nbt.nbt import NBTFile, TAG_List, TAG_Compound
from . import group_blocks_into_fills


def unpack_nbt(tag):
    """
    Unpack an NBT tag into a native Python data structure.
    """
    if isinstance(tag, TAG_List):
        return [unpack_nbt(i) for i in tag.tags]
    elif isinstance(tag, TAG_Compound):
        return {i.name: unpack_nbt(i) for i in tag.tags}
    else:
        return tag.value


def generate(nbt_file, function_file, settings):
    """
    Converts an NBT structure files into an mcfunction file.
    `block_name_map` map can be used to change block name
    (for example when creating a bedrock function).
    Blocks are grouped into fills where possible.
    """
    block_name_map = settings.get('block_name_map', {})
    strip_namespace = settings.get('strip_namespace')

    structure = unpack_nbt(NBTFile(nbt_file, 'rb'))

    # create a list of mapped blocks

    blocks = []

    for block in structure['blocks']:
        x, y, z = block['pos']
        block_data = structure['palette'][block['state']]
        name = block_data['Name']
        if strip_namespace:
            _, name = name.split(':')
        if 'Properties' in block_data:
            properties = [
                f'{key}={value}' for key, value in block_data['Properties'].items()
                # any properties with `false` values are assumed to be default and are ignored
                if value != 'false'
            ]
            name = f"{name}[{','.join(properties)}]"
        # change the block name if a map exists
        if name in block_name_map:
            name = block_name_map[name]
        if name is not None:
            blocks.append((x, y, z, name))

    # try to group contiguous blocks into fills
    fills = group_blocks_into_fills(blocks, structure['size'])

    # write out the function
    with open(function_file, 'w') as file:
        for min_voxel, max_voxel, name in fills:
            min_x, min_y, min_z = min_voxel
            if min_voxel == max_voxel:
                file.write(f'setblock ~{min_x} ~{min_y} ~{min_z} {name}\n')
            else:
                max_x, max_y, max_z = max_voxel
                file.write(f'fill ~{min_x} ~{min_y} ~{min_z} ~{max_x} ~{max_y} ~{max_z} {name}\n')
