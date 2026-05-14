import hou
from pxr import Sdf, Gf, Vt, Usd
from pathlib import Path

def copy_structure_no_values(src_path, dst_path, primpath=''):
    src_stage = Usd.Stage.Open(src_path)
    if not src_stage:
        return

    dst_stage = Usd.Stage.CreateNew(dst_path)
    if not dst_stage:
        return
    
    rule = hou.LopSelectionRule(primpath + '/**')
    paths = rule.expandedPaths(stage = src_stage)

    for path in paths:
        dst_prim = dst_stage.OverridePrim(path)
        src_prim = src_stage.GetPrimAtPath(path)


        for src_attr in src_prim.GetAuthoredAttributes():
            attr_name = src_attr.GetName()
            if attr_name.endswith(':indices'):
                continue
            type_name_sdf = src_attr.GetTypeName() 
            custom = src_attr.IsCustom()           
            variability = src_attr.GetVariability() 


            dst_prim.CreateAttribute(
                attr_name, 
                type_name_sdf, 
                custom, 
                variability
            )

    dst_stage.GetRootLayer().Save()
    
node = hou.pwd()

usd_file_path = node.parm('lopoutput').eval()
manifest_path = '.'.join(usd_file_path.split('.')[:-1] + ['manifest'] + usd_file_path.split('.')[-1:])

manifest_name = manifest_path.split('/')[-1]

primpath = node.parm('primpath').eval()
clip_name = node.parm('clip').eval()
frame_range1 = node.parm('frame_range1').eval()
frame_range2 = node.parm('frame_range2').eval()
scene_range1 = node.parm('scene_range1').eval()
scene_range2 = node.parm('scene_range2').eval()
loop = node.parm('loop').eval()

copy_structure_no_values(usd_file_path, manifest_path, primpath)

file_frame_list = list(range(frame_range1, frame_range2+1))
orig_file_frame_list = file_frame_list
scene_frame_list = list(range(scene_range1, scene_range2+1))

if loop and len(file_frame_list) < len(scene_frame_list):
    mul = len(scene_frame_list) / len(file_frame_list)
    mul = int(mul)+1
    tmp_list = []
    for i in range(mul):
        tmp_list += file_frame_list
    file_frame_list = tmp_list

layer = Sdf.Layer.FindOrOpen(usd_file_path)
prim_spec = layer.GetPrimAtPath(primpath)

clips_info = prim_spec.GetInfo("clips")

active = [(Gf.Vec2d(x, orig_file_frame_list.index(y)))for x,y in list(zip(scene_frame_list, file_frame_list))]
active = Vt.Vec2dArray(active)
manifest_asset_path = Sdf.AssetPath('./' + manifest_name)

clips_info[clip_name]["active"] = active
clips_info[clip_name]["manifestAssetPath"] = manifest_asset_path

prim_spec.SetInfo("clips", clips_info)
layer.Save()

