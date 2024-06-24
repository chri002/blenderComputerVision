import bpy, mathutils



base_path = "C:\\temp\\tempo4"



allowed_types = ['MESH']

bpy.context.view_layer.use_pass_cryptomatte_object = True
bpy.context.scene.use_nodes = True

bpy.context.scene.view_layers[0].use_pass_cryptomatte_object = True

nodes = bpy.context.scene.node_tree.nodes
print(bpy.context.scene.node_tree.bl_idname)
if("CompositorNodeTree" in bpy.context.scene.node_tree.bl_idname):
    for n in nodes:
        if "CompositorNodeRLayers" not in n.bl_idname:
            nodes.remove(n)
            

node_render_layers = nodes["Render Layers"]
node_file_output = nodes.new('CompositorNodeOutputFile')
node_file_output.location = mathutils.Vector((600.0, 460.0))
node_file_output.width = 220
node_file_output.base_path = base_path
node_file_output.format.compression = 100
node_file_output.inputs['Image'].name = 'Render'
node_file_output.file_slots['Image'].path = 'Render'

links = bpy.context.scene.node_tree.links
links.new(node_render_layers.outputs['Image'], node_file_output.inputs['Render'])

i = 0
for obj in bpy.context.view_layer.objects:
    if obj.type not in allowed_types or "Templates" in obj.users_collection[0].name:
        continue
    
    node_cryptomatte = nodes.new('CompositorNodeCryptomatteV2')
    node_cryptomatte.location = mathutils.Vector((300.0, 360.0 - i * 260))
    node_cryptomatte.matte_id = obj.name
    
    node_file_output.file_slots.new(f"{obj.name}_matte")
    
    links.new(node_render_layers.outputs['Image'], node_cryptomatte.inputs['Image'])
    links.new(node_cryptomatte.outputs['Matte'], node_file_output.inputs[f"{obj.name}_matte"])
    i += 1