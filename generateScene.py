import bpy
import random
from mathutils import Vector, Matrix


NAME_COLLISION_TAVOLO = "Tavolo"

NUM_OBJ = 30
LAST_FRAME = 500
POS_LIMIT = [(-1,1),(-1,1),(0,0.1)] # Dynamic X,Y
ROT_INIT = ((-90,90),(-90,90),(-90,90))


def apply_transfrom(ob, use_location=False, use_rotation=False, use_scale=False):
    mb = ob.matrix_basis
    I = Matrix()
    loc, rot, scale = mb.decompose()

    # rotation
    T = Matrix.Translation(loc)
    #R = rot.to_matrix().to_4x4()
    R = mb.to_3x3().normalized().to_4x4()
    S = Matrix.Diagonal(scale).to_4x4()

    transform = [I, I, I]
    basis = [T, R, S]

    def swap(i):
        transform[i], basis[i] = basis[i], transform[i]

    if use_location:
        swap(0)
    if use_rotation:
        swap(1)
    if use_scale:
        swap(2)
        
    M = transform[0] @ transform[1] @ transform[2]
    if hasattr(ob.data, "transform"):
        ob.data.transform(M)
    for c in ob.children:
        c.matrix_local = M @ c.matrix_local
        
    ob.matrix_basis = basis[0] @ basis[1] @ basis[2]



def get_BoundBox(object_name):
    """
    returns the corners of the bounding box of an object in world coordinates
    #  ________ 
    # |\       |\
    # |_\______|_\
    # \ |      \ |
    #  \|_______\|
    # 
    """
    
    ob = bpy.context.scene.objects[object_name]
    bbox_corners = [ob.matrix_world @ Vector(corner) for corner in ob.bound_box]
 
    return bbox_corners
 
 
 
def check_Collision(box1, box2):
    """
    Check Collision of 2 Bounding Boxes
    box1 & box2 muss Liste mit Vector sein,
    welche die Eckpunkte der Bounding Box
    enthält
    #  ________ 
    # |\       |\
    # |_\______|_\
    # \ |      \ |
    #  \|_______\|
    # 
    #
    """
    print('\nKollisionscheck mit:')
 
    x_max = max([e[0] for e in box1])
    x_min = min([e[0] for e in box1])
    y_max = max([e[1] for e in box1])
    y_min = min([e[1] for e in box1])
    z_max = max([e[2] for e in box1])
    z_min = min([e[2] for e in box1])
    print('Box1 min %.2f, %.2f, %.2f' % (x_min, y_min, z_min))
    print('Box1 max %.2f, %.2f, %.2f' % (x_max, y_max, z_max))    
     
    x_max2 = max([e[0] for e in box2])
    x_min2 = min([e[0] for e in box2])
    y_max2 = max([e[1] for e in box2])
    y_min2 = min([e[1] for e in box2])
    z_max2 = max([e[2] for e in box2])
    z_min2 = min([e[2] for e in box2])
    print('Box2 min %.2f, %.2f, %.2f' % (x_min2, y_min2, z_min2))
    print('Box2 max %.2f, %.2f, %.2f' % (x_max2, y_max2, z_max2))        
     
     
    isColliding = ((x_max >= x_min2 and x_max <= x_max2) \
                    or (x_min <= x_max2 and x_min >= x_min2)) \
                    and ((y_max >= y_min2 and y_max <= y_max2) \
                    or (y_min <= y_max2 and y_min >= y_min2)) \
                    and ((z_max >= z_min2 and z_max <= z_max2) \
                    or (z_min <= z_max2 and z_min >= z_min2))
 
         
    return isColliding
 

def out_world(object):
    if  (object.location[0]<POS_LIMIT[0][0] or object.location[0]>POS_LIMIT[0][1]) or (object.location[1]<POS_LIMIT[1][0] or object.location[1]>POS_LIMIT[1][1]) or (object.location[2]<0):
        return True
    

def duplicate(obj, data=True, actions=False, collection=None):
    obj_copy = obj.copy()
    print(obj_copy)
    if data:
        obj_copy.data = obj_copy.data.copy()
    if actions and obj_copy.animation_data:
        obj_copy.animation_data.action = obj_copy.animation_data.action.copy()
    collection.objects.link(obj_copy)
    if(bpy.context.scene.rigidbody_world==None):
        bpy.ops.rigidbody.world_add()
        sc = bpy.context.scene
        sc.rigidbody_world.enabled = True

        collection = bpy.data.collections.new("RigidBody_collection")

        sc.rigidbody_world.collection = collection
        
    bpy.context.scene.rigidbody_world.collection.objects.link(obj_copy)
    
    return obj_copy



def main(context):
    template = [obj for obj in bpy.context.scene.objects if "Templates" in obj.users_collection[0].name and "Tavolo" not in obj.name_full]
    print(template)
    choice = [min(int(random.uniform(0,len(template)+.25)), len(template)-1) for b in range(int(NUM_OBJ))]
    bpy.context.scene.rigidbody_world.enabled = True
        
    collection = bpy.data.collections.new("ElementCollection")
    bpy.context.scene.collection.children.link(collection)
    
    [bpy.context.scene.rigidbody_world.collection.objects.unlink(ob) for ob in bpy.context.scene.rigidbody_world.collection.objects]
    
    tav = duplicate([obj for obj in bpy.context.scene.objects if "Tavolo" in obj.name][0], True, False, collection)
    tav.rigid_body.enabled = False
    
    POS_LIMIT[0] = tuple([-tav.dimensions[0]/2+tav.location[0],tav.dimensions[0]/2+tav.location[0]])
    POS_LIMIT[1] = (-tav.dimensions[1]/2+tav.location[1],tav.dimensions[1]/2+tav.location[1])
    POS_LIMIT[2] = (tav.dimensions[2]/2+tav.location[2],0.5+tav.location[0])
    
    bpy.context.scene.rigidbody_world.point_cache.frame_end = LAST_FRAME
    
    idx = 0
    print(choice)
    for c in choice:
        obj_copy = duplicate(template[int(c)], True, False, collection)
        ok = False
        obj_copy.pass_index = idx
        idx+=1
        
        col_test = 0
        
        while(not(ok) and col_test<10):
            ok = True
            obj_copy.location[0] = random.uniform(POS_LIMIT[0][0],POS_LIMIT[0][1])
            obj_copy.location[1] = random.uniform(POS_LIMIT[1][0],POS_LIMIT[1][1])
            obj_copy.location[2] = random.uniform(POS_LIMIT[2][0],POS_LIMIT[2][1])+obj_copy.dimensions[2]
            obj_copy.rotation_euler[2] = random.uniform(ROT_INIT[2][0], ROT_INIT[2][1])
            obj_copy.rotation_euler[0] = random.uniform(ROT_INIT[0][0], ROT_INIT[0][1])
            obj_copy.rotation_euler[1] = random.uniform(ROT_INIT[1][0], ROT_INIT[1][1])
            
            for ob_t in [obj for obj in bpy.context.scene.objects if "ElementCollection" in obj.users_collection[0].name and "Tavolo" not in obj.name and obj_copy.name not in obj.name]:
                ok = ok and not(check_Collision(get_BoundBox(obj_copy.name), get_BoundBox(ob_t.name)))
            print(obj_copy.name, obj_copy.location)
            col_test +=1
    
    curr_frame = bpy.context.scene.frame_current
    

    bpy.ops.ptcache.free_bake_all()
    for obj in [obj for obj in bpy.context.scene.objects if "ElementCollection" in obj.users_collection[0].name and "Tavolo" not in obj.name]:
        obj.select_set(True)
        
        bpy.context.scene.frame_set(1)
        bpy.ops.ptcache.bake_all(bake=True)
        context = bpy.context # or whatever context you have
        context.scene.frame_set(LAST_FRAME-1)
        
        bpy.ops.object.visual_transform_apply()
        if (out_world(obj)):
            collection.objects.unlink(obj)
        obj.select_set(False)
        
    context.scene.rigidbody_world.enabled = False
               
    
    
main(bpy.context)

 