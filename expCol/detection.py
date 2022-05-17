# -*- coding: utf-8 -*-
import maya.cmds as cmds
import math

def undoWrapper(function):
    """
        undo wrapper (used in decorator)
    """
    def wrapper(*args, **kwargs):
        cmds.undoInfo(ock=True)
        result = function(*args, **kwargs)
        cmds.undoInfo(cck=True)
        return result

    return wrapper

@undoWrapper
def create(parent, input, output, controller, colliders=[], groundCol=False, *args):
    
    if not parent or not input or not output or not controller:
        return
    
    controllerAttr(controller, groundCol)

    #parent_dm = cmds.createNode('decomposeMatrix')
    #cmds.connectAttr(parent + ".worldMatrix[0]", parent_dm + ".inputMatrix", f=True)
    parent_dm = createDecomposeMatrix(parent)
    
    #input_dm = cmds.createNode('decomposeMatrix')
    #cmds.connectAttr(input + ".worldMatrix[0]", input_dm + ".inputMatrix", f=True)
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
    for at1 in 'trs':
        for at2 in 'xyz':
            cmds.setAttr('{}.{}{}'.format(p_radius,at1,at2), l=True, k=False, cb=False)
    cmds.setAttr(p_radius_shape + '.overrideEnabled', 1)
    cmds.setAttr(p_radius_shape + '.overrideDisplayType', 2)
    cmds.connectAttr(controller + '.radius', p_radius_shape + '.radius', f=True)

    colliderExpStr = []
    for j, col in enumerate(colliders):
        if cmds.objExists(col):
            defineStr, detectionStr = setupCollision(col, j, cmds.getAttr(col + '.colliderType'))
            colliderExpStr.append([defineStr, detectionStr])

    # expression string
    expStr = "vector $p0 = <<{0}.outputTranslateX, {0}.outputTranslateY, {0}.outputTranslateZ>>;\n\n".format(parent_dm)
    expStr += "vector $p = <<{0}.outputTranslateX, {0}.outputTranslateY, {0}.outputTranslateZ>>;\n".format(input_dm)
    expStr += "float $p_radius = {0}.radius;\n".format(controller)
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

    expStr += "\t//keep length\n"
    expStr += "\t$p = $p0 + (unit($p - $p0) * $d);\n"

    expStr += "}\n\n"

    # output
    expStr += "{}.input1X = $p.x;\n".format(output_vp)
    expStr += "{}.input1Y = $p.y;\n".format(output_vp)
    expStr += "{}.input1Z = $p.z;\n".format(output_vp)
    
    # create expression
    cmds.expression(s=expStr, name='{}_expCol'.format(input), alwaysEvaluate=False)

def setupCollision(col, index, colliderType, *args):
    defineStr = "//{}\n".format(col)
    detectionStr = "\t//{}\n".format(col)

    if colliderType == 'sphere':
        #dm = cmds.createNode('decomposeMatrix')
        #cmds.connectAttr(col + ".worldMatrix[0]", dm + ".inputMatrix", f=True)
        dm = createDecomposeMatrix(col)

        defineStr += "vector $c{0} = <<{1}.outputTranslateX, {1}.outputTranslateY, {1}.outputTranslateZ>>;\n".format(index, dm)
        defineStr += "float $c{0}_radius = {1}.radius;\n\n".format(index, col)

        detectionStr += "\tif (($c{0}_radius + $p_radius) > mag($p - $c{0}))\n".format(index)
        detectionStr += "\t{\n"
        detectionStr += "\t\t$p = $c{0} + (unit($p - $c{0}) * ($c{0}_radius + $p_radius));\n".format(index)
        detectionStr += "\t}\n\n"

    elif colliderType == 'infinitePlane':
        #dm = cmds.createNode('decomposeMatrix')
        #cmds.connectAttr(col + ".worldMatrix[0]", dm + ".inputMatrix", f=True)
        dm = createDecomposeMatrix(col)
        vp = cmds.ls(cmds.listConnections(col + ".worldMatrix[0]", s=False), type='vectorProduct')
        if vp:
            vp = vp[0]
        else:
            vp = cmds.createNode('vectorProduct')
            cmds.setAttr(vp + '.operation', 3)
            cmds.setAttr(vp + '.input1X', 0)
            cmds.setAttr(vp + '.input1Y', 1)
            cmds.setAttr(vp + '.input1Z', 0)
            cmds.setAttr(vp + '.normalizeOutput', 1)
            cmds.connectAttr(col + ".worldMatrix[0]", vp + ".matrix", f=True)

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
        #dmA = cmds.createNode('decomposeMatrix')
        #dmB = cmds.createNode('decomposeMatrix')
        #cmds.connectAttr(a + ".worldMatrix[0]", dmA + ".inputMatrix", f=True)
        #mds.connectAttr(b + ".worldMatrix[0]", dmB + ".inputMatrix", f=True)
        dmA = createDecomposeMatrix(a)
        dmB = createDecomposeMatrix(b)

        defineStr += "vector $c{0}a = <<{1}.outputTranslateX, {1}.outputTranslateY, {1}.outputTranslateZ>>;\n".format(index, dmA)
        defineStr += "vector $c{0}b = <<{1}.outputTranslateX, {1}.outputTranslateY, {1}.outputTranslateZ>>;\n".format(index, dmB)
        defineStr += "float $c{0}_radius = {1}.radius;\n".format(index, col)
        defineStr += "float $c{0}_height = mag($c{0}b-$c{0}a);\n".format(index)
        defineStr += "vector $c{0}ab = unit($c{0}b-$c{0}a);\n\n".format(index)

        detectionStr += "\tfloat $t{0} = dot($c{0}ab,($p-$c{0}a));\n".format(index)
        detectionStr += "\tif($t{0}/$c{0}_height <= 0)\n".format(index)
        detectionStr += "\t{\n"
        detectionStr += "\t\tif(mag($p-$c{0}a) < ($c{0}_radius + $p_radius))\n".format(index)
        detectionStr += "\t\t\t$p = $c{0}a + (unit($p-$c{0}a) * ($c{0}_radius + $p_radius));\n".format(index)
        detectionStr += "\t}\n"
        detectionStr += "\telse if($t{0}/$c{0}_height >= 1)\n".format(index)
        detectionStr += "\t{\n"
        detectionStr += "\t\tif(mag($p-$c{0}b) < ($c{0}_radius + $p_radius))\n".format(index)
        detectionStr += "\t\t\t$p = $c{0}b + (unit($p-$c{0}b) * ($c{0}_radius + $p_radius));\n".format(index)
        detectionStr += "\t}\n"
        detectionStr += "\telse\n"
        detectionStr += "\t{\n"
        detectionStr += "\t\tvector $q = $c{0}a + ($c{0}ab * $t{0});\n".format(index)
        detectionStr += "\t\tif(mag($p-$q) < ($c{0}_radius + $p_radius))\n".format(index)
        detectionStr += "\t\t\t$p = $q + (unit($p-$q) * ($c{0}_radius + $p_radius));\n".format(index)
        detectionStr += "\t}\n\n"

    elif colliderType == 'capsule2':
        a = cmds.listConnections(col + '.sphereA', d=0)[0]
        b = cmds.listConnections(col + '.sphereB', d=0)[0]
        #dmA = cmds.createNode('decomposeMatrix')
        #dmB = cmds.createNode('decomposeMatrix')
        #cmds.connectAttr(a + ".worldMatrix[0]", dmA + ".inputMatrix", f=True)
        #cmds.connectAttr(b + ".worldMatrix[0]", dmB + ".inputMatrix", f=True)
        dmA = createDecomposeMatrix(a)
        dmB = createDecomposeMatrix(b)

        defineStr += "vector $c{0}a = <<{1}.outputTranslateX, {1}.outputTranslateY, {1}.outputTranslateZ>>;\n".format(index, dmA)
        defineStr += "vector $c{0}b = <<{1}.outputTranslateX, {1}.outputTranslateY, {1}.outputTranslateZ>>;\n".format(index, dmB)
        defineStr += "float $c{0}a_radius = {1}.radiusA;\n".format(index, col)
        defineStr += "float $c{0}b_radius = {1}.radiusB;\n".format(index, col)
        defineStr += "float $c{0}_height = mag($c{0}b-$c{0}a);\n".format(index)
        defineStr += "vector $c{0}ab = unit($c{0}b-$c{0}a);\n\n".format(index)

        detectionStr += "\tfloat $t{0} = dot($c{0}ab,($p-$c{0}a));\n".format(index)
        detectionStr += "\tfloat $ratio{0} = $t{0}/$c{0}_height;\n".format(index)
        detectionStr += "\tif($ratio{0} <= 0)\n".format(index)
        detectionStr += "\t{\n"
        detectionStr += "\t\tif(mag($p-$c{0}a) < ($c{0}a_radius + $p_radius))\n".format(index)
        detectionStr += "\t\t\t$p = $c{0}a + (unit($p-$c{0}a) * ($c{0}a_radius + $p_radius));\n".format(index)
        detectionStr += "\t}\n"
        detectionStr += "\telse if($ratio{0} >= 1)\n".format(index)
        detectionStr += "\t{\n"
        detectionStr += "\t\tif(mag($p-$c{0}b) < ($c{0}b_radius + $p_radius))\n".format(index)
        detectionStr += "\t\t\t$p = $c{0}b + (unit($p-$c{0}b) * ($c{0}b_radius + $p_radius));\n".format(index)
        detectionStr += "\t}\n"
        detectionStr += "\telse\n"
        detectionStr += "\t{\n"
        detectionStr += "\t\tvector $q = $c{0}a + ($c{0}ab * $t{0});\n".format(index)
        detectionStr += "\t\tfloat $r = $c{0}a_radius * (1.0 - $ratio{0}) + $c{0}b_radius * $ratio{0};\n".format(index)
        detectionStr += "\t\tif(mag($p-$q) < ($r + $p_radius))\n".format(index)
        detectionStr += "\t\t\t$p = $q + (unit($p-$q) * ($r + $p_radius));\n".format(index)
        detectionStr += "\t}\n\n"

    return defineStr, detectionStr

def controllerAttr(ctrl, groundCol=False, *args):
    if not cmds.attributeQuery('collision', node=ctrl, ex=True):
        cmds.addAttr(ctrl, ln='collision', nn='__________', at='enum', en='Collision', k=True)
    if not cmds.attributeQuery('colIteration', node=ctrl, ex=True):
        cmds.addAttr(ctrl, ln="colIteration", nn='Colision Iteration', at='long', min=0, dv=3, k=True)
    if not cmds.attributeQuery('radius', node=ctrl, ex=True):
        cmds.addAttr(ctrl, ln="radius", nn='Radius', at='double', min=0, dv=1, k=True)
    if groundCol:
        if not cmds.attributeQuery('groundHeight', node=ctrl, ex=True):
            cmds.addAttr(ctrl, ln="groundHeight", nn='GroundHeight', at='double', dv=0, k=True)

def createDecomposeMatrix(node, *args):
    dm = cmds.ls(cmds.listConnections(node + '.worldMatrix[0]', s=False), type='decomposeMatrix')
    if dm:
        dm = dm[0]
    else:
        dm = cmds.createNode('decomposeMatrix')
        cmds.connectAttr(node + ".worldMatrix[0]", dm + ".inputMatrix", f=True)

    return dm