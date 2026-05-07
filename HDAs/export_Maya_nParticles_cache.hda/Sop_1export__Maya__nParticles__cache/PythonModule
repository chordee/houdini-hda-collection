
import imp
import hou


def cache():
    node = hou.pwd()
    nc = imp.load_source('', node.parm('module_path').eval())
    nc.houdini_export()
