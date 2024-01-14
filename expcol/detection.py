# -*- coding: utf-8 -*-
import maya.cmds as cmds
import math

from .utils import (
    undoWrapper, 
    lockHideAttr, 
    createDecomposeMatrix,
    createUnitVector
)

class CreateConfig:
    
    TYPE = "standard"

    @classmethod
    def set_type(cls, type):
        if type == "customnode":
            try:
                cmds.loadPlugin('colDetectionNode.mll', qt=True)
                print("Set create type to 'customnode' (use colDetectionMtxNode).")
                cls.TYPE = type
            except:
                print("Plugin \"colDetectionNode.mll\" not found.")
                print("Set create type to 'standard' (use expression node).")
                cls.TYPE = "standard"
        else:
            print("Set create type to 'standard' (use expression node).")
            cls.TYPE = "standard"

def create(input, output, controller, *args, **kwargs):
    if CreateConfig.TYPE == "customnode":
        return create_customnode(input, output, controller, *args, **kwargs)
    else:
        return create_standard(input, output, controller, *args, **kwargs)

def add_control_attr(ctrl, *args, **kwargs):
    if CreateConfig.TYPE == "customnode":
        return add_control_attr_customnode(ctrl, *args, **kwargs)
    else:
        return add_control_attr_standard(ctrl, *args, **kwargs)

@undoWrapper
def create_standard(
        input, 
        output, 
        controller, 
        parent=None, 
        colliders=[], 
        groundCol=False, 
        scalable=False, 
        radius_rate=None,
        *args, 
        **kwargs
    ):
    """ create collision detection

    Args:
        input (str): input transform or joint.
        output (str): output transform or joint.
        controller (str): node to add control attributes.
        parent (str, optional): parent transform or joint.
        colliders (list, optional): list of colliders. Defaults to [].
        groundCol (bool, optional): add horizontal plane collision. Defaults to False.
        scalable (bool, optional): allow for parent scale of joint-chain and parent scale of colliders. Defaults to False.
        radius_rate (float, optional): rate at which radius and tip radius are interpolated, between 0 and 1. Defaults to None.

    Returns:
        tuple: Created expression node (exp_node), implicitSphere node for radius visualization (p_radius), and vectorProduct node connected to output (output_vp).
    """
    
    if not input or not output or not controller:
        return
    
    use_tip_radius = not radius_rate is None

    add_control_attr(controller, groundCol, use_tip_radius)

    input_dm = createDecomposeMatrix(input)
    output_vp = cmds.createNode('vectorProduct')
    cmds.setAttr(output_vp + '.operation', 4)
    cmds.setAttr(output_vp + '.normalizeOutput', 0)
    cmds.connectAttr(output + '.parentInverseMatrix[0]', output_vp + '.matrix', f=True)
    cmds.connectAttr(output_vp + '.output', output + '.translate', f=True)

    p_radius_shape = cmds.createNode('implicitSphere')
    p_radius = cmds.listRelatives(p_radius_shape, p=True)[0]
    p_radius = cmds.rename(p_radius, '{}_radius'.format(output))
    p_radius_shape = cmds.listRelatives(p_radius, s=True)[0]
    cmds.parent(p_radius, output, r=True)
    lockHideAttr(p_radius, ['tx','ty','tz','rx','ry','rz'])
    cmds.setAttr(p_radius_shape + '.overrideEnabled', 1)
    cmds.setAttr(p_radius_shape + '.overrideDisplayType', 2)
    

    colliderExpStr = []
    for j, col in enumerate(colliders):
        if cmds.objExists(col):
            defineStr, detectionStr = setupCollision(col, j, cmds.getAttr(col + '.colliderType'), scalable=scalable)
            colliderExpStr.append([defineStr, detectionStr])

    # expression string
    expStr = ""
    
    if parent:
        parent_dm = createDecomposeMatrix(parent)
        expStr += "vector $p0 = <<{0}.outputTranslateX, {0}.outputTranslateY, {0}.outputTranslateZ>>;\n\n".format(parent_dm)
    else:
        input_parent = cmds.listRelatives(input, p=True)
        if input_parent:
            parent_dm = createDecomposeMatrix(input_parent[0])
        else:
            scalable = False
    
    expStr += "vector $p = <<{0}.outputTranslateX, {0}.outputTranslateY, {0}.outputTranslateZ>>;\n".format(input_dm)

    if scalable:
        expStr += "float $p_scaleFactor = abs({0}.outputScaleZ);\n".format(parent_dm)
        if use_tip_radius:
            if radius_rate == 0.0:
                expStr += "float $p_radius = {0}.radius * $p_scaleFactor;\n".format(controller)
            elif radius_rate == 1.0:
                expStr += "float $p_radius = {0}.tipRadius * $p_scaleFactor;\n".format(controller)
            else:
                expStr += "float $p_radius = ({0}.radius*{1} + {0}.tipRadius*{2}) * $p_scaleFactor;\n".format(controller, 1.0-radius_rate, radius_rate)
        else:
            expStr += "float $p_radius = {0}.radius * $p_scaleFactor;\n".format(controller)
        if parent:
            expStr += "float $d = mag($p - $p0);\n\n"
    else:
        if use_tip_radius:
            if radius_rate == 0.0:
                expStr += "float $p_radius = {0}.radius;\n".format(controller)
            elif radius_rate == 1.0:
                expStr += "float $p_radius = {0}.tipRadius;\n".format(controller)
            else:
                expStr += "float $p_radius = {0}.radius*{1} + {0}.tipRadius*{2};\n".format(controller, 1.0-radius_rate, radius_rate)
        else:
            expStr += "float $p_radius = {0}.radius;\n".format(controller)
        if parent:
            vec = []
            vec.append(cmds.getAttr(input_dm + '.outputTranslateX') - cmds.getAttr(parent_dm + '.outputTranslateX'))
            vec.append(cmds.getAttr(input_dm + '.outputTranslateY') - cmds.getAttr(parent_dm + '.outputTranslateY'))
            vec.append(cmds.getAttr(input_dm + '.outputTranslateZ') - cmds.getAttr(parent_dm + '.outputTranslateZ'))
            expStr += "float $d = {};\n\n".format(math.sqrt(vec[0]**2 + vec[1]**2 + vec[2]**2))
    
    # collider define
    for cs in colliderExpStr:
        expStr += cs[0]
    
    # ground height
    if groundCol:
        expStr += "//ground\n"
        expStr += "float $groundHeight = {}.groundHeight;\n\n".format(controller)
    
    # collision iteration
    expStr += "//collision iteration\n"
    expStr += "for($i = 0; $i < {}.colIteration; $i++)\n".format(controller)
    expStr += "{\n"

    for cs in colliderExpStr:
        expStr += cs[1]

    if groundCol:
        expStr += "\t//ground\n"
        expStr += "\tif($p.y < ($groundHeight + $p_radius))\n"
        expStr += "\t{\n"
        expStr += "\t\t$p = <<$p.x, ($groundHeight + $p_radius), $p.z>>;\n"
        expStr += "\t}\n\n"

    if parent:
        expStr += "\t//keep length\n"
        expStr += "\t$p = $p0 + (unit($p - $p0) * $d);\n"

    expStr += "}\n\n"

    # output
    expStr += "{}.input1X = $p.x;\n".format(output_vp)
    expStr += "{}.input1Y = $p.y;\n".format(output_vp)
    expStr += "{}.input1Z = $p.z;\n".format(output_vp)

    if scalable:
        expStr += "{}.scaleX = $p_radius / $p_scaleFactor;\n".format(p_radius)
        expStr += "{}.scaleY = $p_radius / $p_scaleFactor;\n".format(p_radius)
        expStr += "{}.scaleZ = $p_radius / $p_scaleFactor;\n".format(p_radius)
    else:
        expStr += "{}.scaleX = $p_radius;\n".format(p_radius)
        expStr += "{}.scaleY = $p_radius;\n".format(p_radius)
        expStr += "{}.scaleZ = $p_radius;\n".format(p_radius)
    
    # create expression
    exp_node = cmds.expression(s=expStr, name='{}_expCol'.format(input), alwaysEvaluate=False)

    return exp_node, p_radius, output_vp

def setupCollision(col, index, colliderType, scalable=False, *args):
    defineStr = "//{}\n".format(col)
    detectionStr = "\t//{}\n".format(col)

    if colliderType == 'sphere':
        dm = createDecomposeMatrix(col)

        defineStr += "vector $c{0} = <<{1}.outputTranslateX, {1}.outputTranslateY, {1}.outputTranslateZ>>;\n".format(index, dm)
        if scalable:
            defineStr += "float $c{0}_scaleFactor = {1}.outputScaleZ;\n".format(index, dm)
            defineStr += "float $c{0}_radius = {1}.radius * $c{0}_scaleFactor;\n\n".format(index, col)
        else:
            defineStr += "float $c{0}_radius = {1}.radius;\n\n".format(index, col)

        detectionStr += "\tif (($c{0}_radius+$p_radius) * ($c{0}_radius+$p_radius) > dot($p-$c{0}, $p-$c{0}))\n".format(index)
        detectionStr += "\t{\n"
        detectionStr += "\t\t$p = $c{0} + (unit($p - $c{0}) * ($c{0}_radius + $p_radius));\n".format(index)
        detectionStr += "\t}\n\n"

    elif colliderType == 'infinitePlane':
        dm = createDecomposeMatrix(col)
        vp = createUnitVector(col, vec=[0,1,0])

        defineStr += "vector $c{0} = <<{1}.outputTranslateX, {1}.outputTranslateY, {1}.outputTranslateZ>>;\n".format(index, dm)
        defineStr += "vector $c{0}_normal = <<{1}.outputX, {1}.outputY, {1}.outputZ>>;\n\n".format(index, vp)

        detectionStr += "\t$distancePointPlane = dot($c{0}_normal, ($p - $c{0}));\n".format(index)
        detectionStr += "\tif($distancePointPlane - $p_radius < 0)\n"
        detectionStr += "\t{\n"
        detectionStr += "\t\t$p = $p - ($c{0}_normal * ($distancePointPlane - $p_radius));\n".format(index)
        detectionStr += "\t}\n\n"

    elif colliderType == 'capsule':
        a = cmds.listConnections(col + '.sphereA', d=0)[0]
        b = cmds.listConnections(col + '.sphereB', d=0)[0]
        dmA = createDecomposeMatrix(a)
        dmB = createDecomposeMatrix(b)

        defineStr += "vector $c{0}a = <<{1}.outputTranslateX, {1}.outputTranslateY, {1}.outputTranslateZ>>;\n".format(index, dmA)
        defineStr += "vector $c{0}b = <<{1}.outputTranslateX, {1}.outputTranslateY, {1}.outputTranslateZ>>;\n".format(index, dmB)
        if scalable:
            defineStr += "float $c{0}_scaleFactor = {1}.outputScaleZ;\n".format(index, dmA)
            defineStr += "float $c{0}_radius = {1}.radius * $c{0}_scaleFactor;\n".format(index, col)
        else:
            defineStr += "float $c{0}_radius = {1}.radius;\n".format(index, col)
        defineStr += "float $c{0}_height = mag($c{0}b-$c{0}a);\n".format(index)
        defineStr += "vector $c{0}ab = unit($c{0}b-$c{0}a);\n\n".format(index)

        detectionStr += "\tfloat $t{0} = dot($c{0}ab,($p-$c{0}a));\n".format(index)
        detectionStr += "\tfloat $sq_rad_sum{0} = ($c{0}_radius + $p_radius) * ($c{0}_radius + $p_radius);\n".format(index)
        detectionStr += "\tif($t{0}/$c{0}_height <= 0)\n".format(index)
        detectionStr += "\t{\n"
        detectionStr += "\t\tif(dot($p-$c{0}a, $p-$c{0}a) < $sq_rad_sum{0})\n".format(index)
        detectionStr += "\t\t\t$p = $c{0}a + (unit($p-$c{0}a) * ($c{0}_radius + $p_radius));\n".format(index)
        detectionStr += "\t}\n"
        detectionStr += "\telse if($t{0}/$c{0}_height >= 1)\n".format(index)
        detectionStr += "\t{\n"
        detectionStr += "\t\tif(dot($p-$c{0}b, $p-$c{0}b) < $sq_rad_sum{0})\n".format(index)
        detectionStr += "\t\t\t$p = $c{0}b + (unit($p-$c{0}b) * ($c{0}_radius + $p_radius));\n".format(index)
        detectionStr += "\t}\n"
        detectionStr += "\telse\n"
        detectionStr += "\t{\n"
        detectionStr += "\t\tvector $q = $c{0}a + ($c{0}ab * $t{0});\n".format(index)
        detectionStr += "\t\tif(dot($p-$q, $p-$q) < $sq_rad_sum{0})\n".format(index)
        detectionStr += "\t\t\t$p = $q + (unit($p-$q) * ($c{0}_radius + $p_radius));\n".format(index)
        detectionStr += "\t}\n\n"

    elif colliderType == 'capsule2':
        a = cmds.listConnections(col + '.sphereA', d=0)[0]
        b = cmds.listConnections(col + '.sphereB', d=0)[0]
        dmA = createDecomposeMatrix(a)
        dmB = createDecomposeMatrix(b)

        defineStr += "vector $c{0}a = <<{1}.outputTranslateX, {1}.outputTranslateY, {1}.outputTranslateZ>>;\n".format(index, dmA)
        defineStr += "vector $c{0}b = <<{1}.outputTranslateX, {1}.outputTranslateY, {1}.outputTranslateZ>>;\n".format(index, dmB)
        if scalable:
            defineStr += "float $c{0}_scaleFactor = {1}.outputScaleZ;\n".format(index, dmA)
            defineStr += "float $c{0}a_radius = {1}.radiusA * $c{0}_scaleFactor;\n".format(index, col)
            defineStr += "float $c{0}b_radius = {1}.radiusB * $c{0}_scaleFactor;\n".format(index, col)
        else:
            defineStr += "float $c{0}a_radius = {1}.radiusA;\n".format(index, col)
            defineStr += "float $c{0}b_radius = {1}.radiusB;\n".format(index, col)
        defineStr += "float $c{0}_height = mag($c{0}b-$c{0}a);\n".format(index)
        defineStr += "vector $c{0}ab = unit($c{0}b-$c{0}a);\n\n".format(index)

        detectionStr += "\tfloat $t{0} = dot($c{0}ab,($p-$c{0}a));\n".format(index)
        detectionStr += "\tfloat $ratio{0} = $t{0}/$c{0}_height;\n".format(index)
        detectionStr += "\tif($ratio{0} <= 0)\n".format(index)
        detectionStr += "\t{\n"
        detectionStr += "\t\tif(dot($p-$c{0}a, $p-$c{0}a) < ($c{0}a_radius + $p_radius) * ($c{0}a_radius + $p_radius))\n".format(index)
        detectionStr += "\t\t\t$p = $c{0}a + (unit($p-$c{0}a) * ($c{0}a_radius + $p_radius));\n".format(index)
        detectionStr += "\t}\n"
        detectionStr += "\telse if($ratio{0} >= 1)\n".format(index)
        detectionStr += "\t{\n"
        detectionStr += "\t\tif(dot($p-$c{0}b, $p-$c{0}b) < ($c{0}b_radius + $p_radius) * ($c{0}b_radius + $p_radius))\n".format(index)
        detectionStr += "\t\t\t$p = $c{0}b + (unit($p-$c{0}b) * ($c{0}b_radius + $p_radius));\n".format(index)
        detectionStr += "\t}\n"
        detectionStr += "\telse\n"
        detectionStr += "\t{\n"
        detectionStr += "\t\tvector $q = $c{0}a + ($c{0}ab * $t{0});\n".format(index)
        detectionStr += "\t\tfloat $r = $c{0}a_radius * (1.0 - $ratio{0}) + $c{0}b_radius * $ratio{0};\n".format(index)
        detectionStr += "\t\tif(dot($p-$q, $p-$q) < ($r + $p_radius) * ($r + $p_radius))\n".format(index)
        detectionStr += "\t\t\t$p = $q + (unit($p-$q) * ($r + $p_radius));\n".format(index)
        detectionStr += "\t}\n\n"
    
    elif colliderType == 'cuboid':
        dm = createDecomposeMatrix(col)
        
        # unit vector
        vp_x = createUnitVector(col, vec=[1,0,0])
        vp_y = createUnitVector(col, vec=[0,1,0])
        vp_z = createUnitVector(col, vec=[0,0,1])

        # define
        defineStr += "vector $c{0} = <<{1}.outputTranslateX, {1}.outputTranslateY, {1}.outputTranslateZ>>;\n".format(index, dm)
        defineStr += "vector $c{0}_vx = <<{1}.outputX, {1}.outputY, {1}.outputZ>>;\n".format(index, vp_x)
        defineStr += "vector $c{0}_vy = <<{1}.outputX, {1}.outputY, {1}.outputZ>>;\n".format(index, vp_y)
        defineStr += "vector $c{0}_vz = <<{1}.outputX, {1}.outputY, {1}.outputZ>>;\n".format(index, vp_z)
        if scalable:
            defineStr += "float $c{0}_scaleFactor = {1}.outputScaleZ;\n".format(index, dm)
            defineStr += "float $c{0}_w = {1}.width / 2.0 * $c{0}_scaleFactor;\n".format(index, col)
            defineStr += "float $c{0}_h = {1}.height / 2.0 * $c{0}_scaleFactor;\n".format(index, col)
            defineStr += "float $c{0}_d = {1}.depth / 2.0 * $c{0}_scaleFactor;\n\n".format(index, col)
        else:
            defineStr += "float $c{0}_w = {1}.width / 2.0;\n".format(index, col)
            defineStr += "float $c{0}_h = {1}.height / 2.0;\n".format(index, col)
            defineStr += "float $c{0}_d = {1}.depth / 2.0;\n\n".format(index, col)

        defineStr += "vector $c{0}_cp = <<0,0,0>>;\n".format(index)
        defineStr += "float $c{0}_lx = 0;\n".format(index)
        defineStr += "float $c{0}_ly = 0;\n".format(index)
        defineStr += "float $c{0}_lz = 0;\n".format(index)
        defineStr += "float $c{0}_min_l = 99999;\n".format(index)
        defineStr += "int $c{0}_hit = 1;\n\n".format(index)

        # detection
        detectionStr += "\t$c{0}_cp = $p - $c{0};\n".format(index)
        detectionStr += "\t$c{0}_lx = dot($c{0}_vx, $c{0}_cp);\n".format(index)
        detectionStr += "\t$c{0}_ly = dot($c{0}_vy, $c{0}_cp);\n".format(index)
        detectionStr += "\t$c{0}_lz = dot($c{0}_vz, $c{0}_cp);\n".format(index)
        detectionStr += "\tif ($c{0}_lx != 0){{if (abs(($c{0}_w + $p_radius) / $c{0}_lx) < 1.0) {{$c{0}_hit = 0;}}}}\n".format(index)
        detectionStr += "\tif ($c{0}_ly != 0){{if (abs(($c{0}_h + $p_radius) / $c{0}_ly) < 1.0) {{$c{0}_hit = 0;}}}}\n".format(index)
        detectionStr += "\tif ($c{0}_lz != 0){{if (abs(($c{0}_d + $p_radius) / $c{0}_lz) < 1.0) {{$c{0}_hit = 0;}}}}\n".format(index)
        detectionStr += "\n"
        detectionStr += "\tif ($c{0}_hit) {{\n".format(index)
        detectionStr += "\t\tif ($c{0}_lx != 0){{$c{0}_min_l = abs(($c{0}_w + $p_radius) / $c{0}_lx);}}\n".format(index)
        detectionStr += "\t\tif ($c{0}_ly != 0){{$c{0}_min_l = min($c{0}_min_l, abs(($c{0}_h + $p_radius) / $c{0}_ly));}}\n".format(index)
        detectionStr += "\t\tif ($c{0}_lz != 0){{$c{0}_min_l = min($c{0}_min_l, abs(($c{0}_d + $p_radius) / $c{0}_lz));}}\n".format(index)
        detectionStr += "\t\tif ($c{0}_min_l == 99999){{\n".format(index)
        detectionStr += "\t\t\t$p = $c{0} + <<$c{0}_w + $p_radius, 0, 0>>;\n".format(index)
        detectionStr += "\t\t} else {\n"
        detectionStr += "\t\t\t$p = $c{0} + ($c{0}_cp * $c{0}_min_l);\n".format(index)
        detectionStr += "\t\t}\n"
        detectionStr += "\t}\n\n"

    return defineStr, detectionStr

@undoWrapper
def create_customnode(
        input, 
        output, 
        controller, 
        parent, 
        colliders=[], 
        radius_rate=None,
        *args, 
        **kwargs
    ):
    """ create collision detection using "colDetectionNode.mll"

    Args:
        input (str): input transform or joint.
        output (str): output transform or joint.
        controller (str): node to add control attributes.
        parent (str): parent transform or joint.
        colliders (list, optional): list of colliders. Defaults to [].
        radius_rate (float, optional): rate at which radius and tip radius are interpolated, between 0 and 1. Defaults to None.

    Returns:
        tuple: Created colDetectionMtxNode, implicitSphere node for radius visualization (p_radius), and vectorProduct node connected to output (output_vp).
    """

    if not input or not output or not controller or not parent:
        return
    
    use_tip_radius = not radius_rate is None

    add_control_attr(controller, use_tip_radius)

    output_vp = cmds.createNode('vectorProduct')
    cmds.setAttr(output_vp + '.operation', 4)
    cmds.setAttr(output_vp + '.normalizeOutput', 0)
    cmds.connectAttr(output + '.parentInverseMatrix[0]', output_vp + '.matrix', f=True)
    cmds.connectAttr(output_vp + '.output', output + '.translate', f=True)

    p_radius_shape = cmds.createNode('implicitSphere')
    p_radius = cmds.listRelatives(p_radius_shape, p=True)[0]
    p_radius = cmds.rename(p_radius, '{}_radius'.format(output))
    p_radius_shape = cmds.listRelatives(p_radius, s=True)[0]
    cmds.parent(p_radius, output, r=True)
    lockHideAttr(p_radius, ['tx','ty','tz','rx','ry','rz'])
    cmds.setAttr(p_radius_shape + '.overrideEnabled', 1)
    cmds.setAttr(p_radius_shape + '.overrideDisplayType', 2)

    detection_node = cmds.createNode('colDetectionMtxNode')
    
    cmds.connectAttr(controller + ".colIteration", detection_node + ".iterations", f=True)
    cmds.connectAttr(controller + ".groundHeight", detection_node + ".groundHeight", f=True)
    cmds.connectAttr(controller + ".groundCollision", detection_node + ".enableGroundCol", f=True)

    if use_tip_radius:
        if radius_rate == 0.0:
            cmds.connectAttr(controller + ".radius", detection_node + ".radius", f=True)
            cmds.connectAttr(controller + ".radius", p_radius + ".scaleX", f=True)
            cmds.connectAttr(controller + ".radius", p_radius + ".scaleY", f=True)
            cmds.connectAttr(controller + ".radius", p_radius + ".scaleZ", f=True)
        elif radius_rate == 1.0:
            cmds.connectAttr(controller + ".tipRadius", detection_node + ".radius", f=True)
            cmds.connectAttr(controller + ".tipRadius", p_radius + ".scaleX", f=True)
            cmds.connectAttr(controller + ".tipRadius", p_radius + ".scaleY", f=True)
            cmds.connectAttr(controller + ".tipRadius", p_radius + ".scaleZ", f=True)
        else:
            try:
                lerp = cmds.createNode('lerp')
                cmds.setAttr(lerp + ".weight", radius_rate)
                cmds.connectAttr(controller + ".radius", lerp + ".input1", f=True)
                cmds.connectAttr(controller + ".tipRadius", lerp + ".input2", f=True)
                cmds.connectAttr(lerp + ".output", detection_node + ".radius", f=True)
                cmds.connectAttr(lerp + ".output", p_radius + ".scaleX", f=True)
                cmds.connectAttr(lerp + ".output", p_radius + ".scaleY", f=True)
                cmds.connectAttr(lerp + ".output", p_radius + ".scaleZ", f=True)
            except:
                bl = cmds.createNode('blendColors')
                cmds.setAttr(bl + ".blender", radius_rate)
                cmds.connectAttr(controller + ".radius", bl + ".color2R", f=True)
                cmds.connectAttr(controller + ".tipRadius", bl + ".color1R", f=True)
                cmds.connectAttr(bl + ".outputR", detection_node + ".radius", f=True)
                cmds.connectAttr(bl + ".outputR", p_radius + ".scaleX", f=True)
                cmds.connectAttr(bl + ".outputR", p_radius + ".scaleY", f=True)
                cmds.connectAttr(bl + ".outputR", p_radius + ".scaleZ", f=True)
    else:
        cmds.connectAttr(controller + ".radius", detection_node + ".radius", f=True)
        cmds.connectAttr(controller + ".radius", p_radius + ".scaleX", f=True)
        cmds.connectAttr(controller + ".radius", p_radius + ".scaleY", f=True)
        cmds.connectAttr(controller + ".radius", p_radius + ".scaleZ", f=True)

    cmds.connectAttr(detection_node + ".output", output_vp + '.input1', f=True)
    cmds.connectAttr(input + ".worldMatrix[0]", detection_node + ".inputMatrix", f=True)
    cmds.connectAttr(parent + ".worldMatrix[0]", detection_node + ".parentMatrix", f=True)

    try: # colDetectionNode <= 1.1.0
        input_world_pos = cmds.xform(input, q=True, ws=True, t=True)
        parent_world_pos = cmds.xform(parent, q=True, ws=True, t=True)
        vec = [
            input_world_pos[0] - parent_world_pos[0],
            input_world_pos[1] - parent_world_pos[1],
            input_world_pos[2] - parent_world_pos[2],
        ]
        cmds.setAttr(detection_node + ".distance", math.sqrt(vec[0]**2 + vec[1]**2 + vec[2]**2))
    except: # colDetectionNode >= 1.2.0
        # "distance" attribute is obsolete in colDetectionMtxNode 1.2.0 and later.
        pass
    
    sphere_col_idx = 0
    capsule_col_idx = 0
    iplane_col_cidx = 0
    
    for col in colliders:
        
        if not cmds.objExists(col):
            continue

        colliderType = cmds.getAttr(col + '.colliderType')
        
        if colliderType == 'sphere':
            cmds.connectAttr(col + ".worldMatrix[0]", detection_node + ".sphereCollider[{}].sphereColMatrix".format(sphere_col_idx), f=True)
            cmds.connectAttr(col + ".radius", detection_node + ".sphereCollider[{}].sphereColRadius".format(sphere_col_idx), f=True)
            sphere_col_idx += 1
        
        elif colliderType == 'capsule' or colliderType == 'capsule2':
            if colliderType == 'capsule' :
                radius_attr_a = ".radius"
                radius_attr_b = ".radius"
            else:
                radius_attr_a = ".radiusA"
                radius_attr_b = ".radiusB"
            
            a = cmds.listConnections(col + '.sphereA', d=0)[0]
            b = cmds.listConnections(col + '.sphereB', d=0)[0]
            cmds.connectAttr(a + ".worldMatrix[0]", detection_node + ".capsuleCollider[{}].capsuleColMatrixA".format(capsule_col_idx), f=True)
            cmds.connectAttr(b + ".worldMatrix[0]", detection_node + ".capsuleCollider[{}].capsuleColMatrixB".format(capsule_col_idx), f=True)
            cmds.connectAttr(col + radius_attr_a, detection_node + ".capsuleCollider[{}].capsuleColRadiusA".format(capsule_col_idx), f=True)
            cmds.connectAttr(col + radius_attr_b, detection_node + ".capsuleCollider[{}].capsuleColRadiusB".format(capsule_col_idx), f=True)
            capsule_col_idx += 1
        
        elif colliderType == 'infinitePlane':
            cmds.connectAttr(col + ".worldMatrix[0]", detection_node + ".infinitePlaneCollider[{}].infinitePlaneColMatrix".format(sphere_col_idx), f=True)
            iplane_col_cidx += 1
    
    return detection_node, p_radius, output_vp

@undoWrapper
def add_control_attr_standard(ctrl, groundCol=False, tip_radius=False, *args, **kwargs):
    if not cmds.attributeQuery('collision', node=ctrl, ex=True):
        cmds.addAttr(ctrl, ln='collision', nn='__________', at='enum', en='Collision', k=True)
    if not cmds.attributeQuery('colIteration', node=ctrl, ex=True):
        cmds.addAttr(ctrl, ln="colIteration", nn='Collision Iteration', at='long', min=0, dv=3, k=True)
    if not cmds.attributeQuery('radius', node=ctrl, ex=True):
        cmds.addAttr(ctrl, ln="radius", nn='Radius', at='double', min=0, dv=1, k=True)
    if tip_radius:
        if not cmds.attributeQuery('tipRadius', node=ctrl, ex=True):
            cmds.addAttr(ctrl, ln="tipRadius", nn='Tip Radius', at='double', min=0, dv=1, k=True)
    if groundCol:
        if not cmds.attributeQuery('groundHeight', node=ctrl, ex=True):
            cmds.addAttr(ctrl, ln="groundHeight", nn='Ground Height', at='double', dv=0, k=True)

@undoWrapper
def add_control_attr_customnode(ctrl, tip_radius=False, *args, **kwargs):
    if not cmds.attributeQuery('collision', node=ctrl, ex=True):
        cmds.addAttr(ctrl, ln='collision', nn='__________', at='enum', en='Collision', k=True)
    if not cmds.attributeQuery('colIteration', node=ctrl, ex=True):
        cmds.addAttr(ctrl, ln="colIteration", nn='Collision Iteration', at='long', min=0, dv=3, k=True)
    if not cmds.attributeQuery('radius', node=ctrl, ex=True):
        cmds.addAttr(ctrl, ln="radius", nn='Radius', at='double', min=0, dv=1, k=True)
    if tip_radius:
        if not cmds.attributeQuery('tipRadius', node=ctrl, ex=True):
            cmds.addAttr(ctrl, ln="tipRadius", nn='Tip Radius', at='double', min=0, dv=1, k=True)
    if not cmds.attributeQuery('groundCollision', node=ctrl, ex=True):
        cmds.addAttr(ctrl, ln="groundCollision", nn='Ground Collision', at='bool', dv=True, k=True)
    if not cmds.attributeQuery('groundHeight', node=ctrl, ex=True):
        cmds.addAttr(ctrl, ln="groundHeight", nn='Ground Height', at='double', dv=0, k=True)

