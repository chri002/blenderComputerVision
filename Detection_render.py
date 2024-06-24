import bpy
import os, sys
from mathutils import Vector



class Box:

    dim_x = 1
    dim_y = 1

    def __init__(self, min_x, min_y, max_x, max_y, dim_x=dim_x, dim_y=dim_y):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        self.dim_x = dim_x
        self.dim_y = dim_y

    @property
    def x(self):
        return round(self.min_x * self.dim_x)

    @property
    def y(self):
        return round(self.dim_y - self.max_y * self.dim_y)

    @property
    def width(self):
        return round((self.max_x - self.min_x) * self.dim_x)

    @property
    def height(self):
        return round((self.max_y - self.min_y) * self.dim_y)
    
    def to_tuple(self):
        if self.width == 0 or self.height == 0:
            return (0, 0, 0, 0)
        return (self.x, self.y, self.width, self.height)


def camera_view_bounds_2d(scene, cam_ob, me_ob):
    """
    Returns camera space bounding box of mesh object.

    Negative 'z' -> the point is behind the camera.

    Takes shift-x/y, lens angle and sensor size into account
    as well as perspective/ortho projections.

    :arg scene: Scene to use for frame size.
    :type scene: :class:`bpy.types.Scene`
    :arg obj: Camera object.
    :type obj: :class:`bpy.types.Object`
    :arg me: Untransformed Mesh.
    :type me: :class:`bpy.types.Mesh´
    :return: a Box object (call its to_tuple() method to get x, y, width and height)
    :rtype: :class:`Box`
    """
    
    mat = cam_ob.matrix_world.normalized().inverted()
    me = me_ob.to_mesh(preserve_all_data_layers=True)
    me.transform(me_ob.matrix_world)
    me.transform(mat)

    camera = cam_ob.data
    frame = [-v for v in camera.view_frame(scene=scene)[:3]]
    camera_persp = camera.type != 'ORTHO'

    lx = []
    ly = []

    for v in me.vertices:
        co_local = v.co
        z = -co_local.z

        if camera_persp:
            if z == 0.0:
                lx.append(0.5)
                ly.append(0.5)
            #if z <= 0.0:
            #    continue
            else:
                frame = [(v / (v.z / z)) for v in frame]

        min_x, max_x = frame[1].x, frame[2].x
        min_y, max_y = frame[0].y, frame[1].y

        x = (co_local.x - min_x) / (max_x - min_x)
        y = (co_local.y - min_y) / (max_y - min_y)

        lx.append(x)
        ly.append(y)

    min_x = clamp(min(lx), 0.0, 1.0)
    max_x = clamp(max(lx), 0.0, 1.0)
    min_y = clamp(min(ly), 0.0, 1.0)
    max_y = clamp(max(ly), 0.0, 1.0)

    #bpy.data.meshes.remove(me)

    r = scene.render
    fac = r.resolution_percentage * 0.01
    dim_x = r.resolution_x * fac
    dim_y = r.resolution_y * fac

    return Box(min_x, min_y, max_x, max_y, dim_x, dim_y)


def clamp(x, minimum, maximum):
    return max(minimum, min(x, maximum))


def write_bounds_2d(filepath, scene, cam_ob, me_obs, frame_start, frame_end, frame_step):
    
    template = [str(obj.name) for obj in bpy.context.scene.objects if "Templates" in obj.users_collection[0].name and "Tavolo" not in obj.name_full]
    print(template)
    with open(filepath, "w") as file: 
        for frame in range(frame_start, frame_end + 1, frame_step):
            indexes = []
            classes = []
            bpy.context.scene.frame_set(frame)
            file.write("[{'frame_id':"+str(frame)+", 'classes':["+",".join(template)+"], 'boxes':[" )
            render("\\".join(filepath.split("\\")[0:-1]), 'render'+str("{:0="+str(len(str(frame))+1)+"}").format(frame)+'.jpg')
            
            for (idx,me_ob) in enumerate(me_obs):
                file.write("[%i %i %i %i]" % (camera_view_bounds_2d(scene, cam_ob, me_ob).to_tuple()))
                indexes.append(str(me_ob.pass_index))
                classes.append(str(template.index([idx for idx in template if me_ob.name.split(".")[0]==(idx.split(".")[0])][0])))
                if(idx<len(me_obs)-1):
                    file.write(",")
            
            file.write("], 'index':["+",".join(indexes)+"], 'class':["+",".join(classes)+"]}")
            if(frame+frame_step>frame_end):
                file.write("]")
            else:
                file.write(",\n")
            
            
            
def render(output_dir, output_file_pattern_string = 'render.jpg'):
    bpy.context.scene.render.filepath = os.path.join(output_dir, (output_file_pattern_string))
    print(os.path.join(output_dir, (output_file_pattern_string)))
    bpy.ops.render.render(write_still = True)


def main(context, main_folder=r"C:\temp\Det_prova4"):
    
    if(not(os.path.exists(main_folder))):
        os.makedirs(main_folder)
    
    filepath = os.path.join(main_folder,r"bounds_2d.txt")

    scene = context.scene
    cam_ob = scene.camera
    me_obs = [obj for obj in context.scene.objects if obj.pass_index>0 and "Templates" not in obj.users_collection[0].name]
    print(me_obs)

    frame_current = scene.frame_current
    frame_start = scene.frame_start
    frame_end = scene.frame_end
    frame_step = scene.frame_step 
    

    write_bounds_2d(filepath, scene, cam_ob, me_obs, frame_start, frame_end, frame_step)

    scene.frame_set(frame_current)
    

main(bpy.context)