# -*- coding: utf-8 -*-
import maya.cmds as cmds

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

def getUniqueName(n, *args):
    flag = True
    i = 1
    while flag:
        if cmds.objExists('{}{}'.format(n,i)):
            i += 1
        else:
            flag = False

    return '{}{}'.format(n,i)

def lockHideAttr(obj, attr, *args):
    if type(attr) == str:
        if attr == 'all':
            for at1 in 'trs':
                for at2 in 'xyz':
                    cmds.setAttr('{}.{}{}'.format(obj,at1,at2), l=True, k=False, cb=False)
            cmds.setAttr('{}.v'.format(obj), l=True, k=False, cb=False)
    else:
        for at in attr:
            cmds.setAttr('{}.{}'.format(obj,at), l=True, k=False, cb=False)

def disableRenderStats(obj, *args):
    sh = cmds.listRelatives(obj, s=True)[0]
    cmds.setAttr(sh + '.castsShadows', 0)
    cmds.setAttr(sh + '.receiveShadows', 0)
    cmds.setAttr(sh + '.holdOut', 0)
    cmds.setAttr(sh + '.motionBlur', 0)
    cmds.setAttr(sh + '.primaryVisibility', 0)
    cmds.setAttr(sh + '.smoothShading', 0)
    cmds.setAttr(sh + '.visibleInReflections', 0)
    cmds.setAttr(sh + '.visibleInRefractions', 0)
    cmds.setAttr(sh + '.doubleSided', 0)

def setOverrideColor(obj, colIdx, *args):
    cmds.setAttr(obj + '.overrideEnabled', True)
    cmds.setAttr(obj + '.overrideRGBColors', False)
    cmds.setAttr(obj + '.overrideColor', colIdx)

def setOutlinerColor(obj, col=[0,0,0], *args):
    cmds.setAttr(obj + '.useOutlinerColor', True)
    cmds.setAttr(obj + '.outlinerColor', col[0], col[1], col[2])

def createDecomposeMatrix(node, *args):
    dm = cmds.ls(cmds.listConnections(node + '.worldMatrix[0]', s=False), type='decomposeMatrix')
    if dm:
        dm = dm[0]
    else:
        dm = cmds.createNode('decomposeMatrix')
        cmds.connectAttr(node + ".worldMatrix[0]", dm + ".inputMatrix", f=True)

    return dm

def createUnitVector(node, vec=[1,0,0], *args):
    vp = cmds.createNode('vectorProduct')
    cmds.setAttr(vp + '.operation', 3)
    cmds.setAttr(vp + '.input1X', vec[0])
    cmds.setAttr(vp + '.input1Y', vec[1])
    cmds.setAttr(vp + '.input1Z', vec[2])
    cmds.setAttr(vp + '.normalizeOutput', 1)
    cmds.connectAttr(node + ".worldMatrix[0]", vp + ".matrix", f=True)
    return vp
