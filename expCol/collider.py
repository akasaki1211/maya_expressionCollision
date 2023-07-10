# -*- coding: utf-8 -*-
import maya.cmds as cmds

from .utils import (
    undoWrapper,
    getUniqueName,
    lockHideAttr,
    disableRenderStats,
    setOverrideColor,
    setOutlinerColor
)

@undoWrapper
def iplane(*args):
    root, makePlane = cmds.nurbsPlane(ax=[0,1,0], w=1, lr=1, d=3, u=1, v=1, n=getUniqueName('infinitePlaneCollider'))
    addCommonAttr(root, 'infinitePlane')
    setOutlinerColor(root, [1,1,0])
    disableRenderStats(root)

    # connectAttr
    sh = cmds.listRelatives(root, s=True)[0]
    setOverrideColor(sh, 17)
    cmds.connectAttr(root + '.displayType', sh + '.overrideDisplayType', f=True)

    return root

@undoWrapper
def sphere(*args):
    root, makeSphere = cmds.sphere(s=8, nsp=4, ax=[0,1,0], n=getUniqueName('sphereCollider'))
    lockHideAttr(root, ['sx','sy','sz'])
    addCommonAttr(root, 'sphere')
    cmds.addAttr(root, ln='radius', nn='Radius', at='double', dv=0.5, min=0.001, k=True)
    setOutlinerColor(root, [1,1,0])
    disableRenderStats(root)

    # connectAttr
    cmds.connectAttr(root + '.radius', makeSphere + '.radius', f=True)
    sh = cmds.listRelatives(root, s=True)[0]
    setOverrideColor(sh, 17)
    cmds.connectAttr(root + '.displayType', sh + '.overrideDisplayType', f=True)

    return root
    
@undoWrapper
def capsule(*args):
    root = cmds.createNode('transform', n=getUniqueName('capsuleCollider'))
    lockHideAttr(root, ['sx','sy','sz'])
    addCommonAttr(root, 'capsule', 'sphereA', 'sphereB', 'cylinder')
    cmds.addAttr(root, ln='radius', nn='Radius', at='double', dv=0.5, min=0.001, k=True)
    cmds.addAttr(root, ln='height', nn='Height', at='double', dv=2.0, min=0.001, k=True)
    setOutlinerColor(root, [1,1,0])

    # sphere, cylinder
    sphere1 = cmds.sphere(ssw=180, esw=360, nsp=8, ax=[1,0,0])
    sphere2 = cmds.sphere(ssw=0, esw=180, nsp=8, ax=[1,0,0])
    cylinder = cmds.cylinder(s=16, ax=[0,1,0])
    cmds.parent(sphere1[0], root, r=1)
    cmds.parent(sphere2[0], root, r=1)
    cmds.parent(cylinder[0], root, r=1)
    setOverrideColor(sphere1[0], 17)
    setOverrideColor(sphere2[0], 17)
    setOverrideColor(cylinder[0], 17)

    lockHideAttr(sphere1[0], ['tx','tz','rx','ry','rz','sx','sy','sz','v'])
    lockHideAttr(sphere2[0], ['tx','tz','rx','ry','rz','sx','sy','sz','v'])
    lockHideAttr(cylinder[0], 'all')
    disableRenderStats(sphere1[0])
    disableRenderStats(sphere2[0])
    disableRenderStats(cylinder[0])

    # md node
    md1 = cmds.createNode('multiplyDivide')
    md2 = cmds.createNode('multiplyDivide')
    md3 = cmds.createNode('multiplyDivide')
    cmds.setAttr(md1 + ".operation", 1)
    cmds.setAttr(md1 + ".input2X", 0.5)
    cmds.setAttr(md2 + ".operation", 1)
    cmds.setAttr(md2 + ".input2X", -0.5)
    cmds.setAttr(md3 + ".operation", 2)

    # connectAttr
    cmds.connectAttr("{}.message".format(sphere1[0]), "{}.{}".format(root, 'sphereA'))
    cmds.connectAttr("{}.message".format(sphere2[0]), "{}.{}".format(root, 'sphereB'))
    cmds.connectAttr("{}.message".format(cylinder[0]), "{}.{}".format(root, 'cylinder'))

    cmds.connectAttr(md1 + '.outputX', sphere1[0] + '.ty', f=True)
    cmds.connectAttr(md2 + '.outputX', sphere2[0] + '.ty', f=True)
    cmds.connectAttr(md3 + '.outputX', cylinder[1] + '.heightRatio', f=True)
    
    cmds.connectAttr(root + '.height', md1 + '.input1X', f=True)
    cmds.connectAttr(root + '.height', md2 + '.input1X', f=True)
    cmds.connectAttr(root + '.height', md3 + '.input1X', f=True)
    cmds.connectAttr(root + '.radius', md3 + '.input2X', f=True)
    cmds.connectAttr(root + '.radius', sphere1[1] + '.radius', f=True)
    cmds.connectAttr(root + '.radius', sphere2[1] + '.radius', f=True)
    cmds.connectAttr(root + '.radius', cylinder[1] + '.radius', f=True)
    cmds.connectAttr(root + '.displayType', sphere1[0] + '.overrideDisplayType', f=True)
    cmds.connectAttr(root + '.displayType', sphere2[0] + '.overrideDisplayType', f=True)
    cmds.connectAttr(root + '.displayType', cylinder[0] + '.overrideDisplayType', f=True)

    return root

@undoWrapper
def capsule2(*args):
    root = cmds.createNode('transform', n=getUniqueName('capsule2Collider'))
    lockHideAttr(root, ['sx','sy','sz'])
    addCommonAttr(root, 'capsule2', 'sphereA', 'sphereB', 'circleA', 'circleB', 'loftedSurface')
    cmds.addAttr(root, ln='radiusA', nn='Radius A', at='double', dv=0.5, min=0.001, k=True)
    cmds.addAttr(root, ln='radiusB', nn='Radius B', at='double', dv=0.5, min=0.001, k=True)
    cmds.addAttr(root, ln='height', nn='Height', at='double', dv=2.0, min=0.001, k=True)
    setOutlinerColor(root, [1,1,0])

    # sphere, circle, loft
    sphere1 = cmds.sphere(ssw=180, esw=360, nsp=8, ax=[1,0,0])
    sphere2 = cmds.sphere(ssw=0, esw=180, nsp=8, ax=[1,0,0])
    circle1 = cmds.circle(s=16, nr=[0,1,0])
    circle2 = cmds.circle(s=16, nr=[0,1,0])
    loftedSurface = cmds.loft(circle1[0], circle2[0])
    cmds.parent(sphere1[0], root, r=1)
    cmds.parent(sphere2[0], root, r=1)
    cmds.parent(circle1[0], root, r=1)
    cmds.parent(circle2[0], root, r=1)
    cmds.parent(loftedSurface[0], root, r=1)
    setOverrideColor(sphere1[0], 17)
    setOverrideColor(sphere2[0], 17)
    setOverrideColor(loftedSurface[0], 17)
    cmds.setAttr(circle1[0] + '.v', 0)
    cmds.setAttr(circle2[0] + '.v', 0)

    lockHideAttr(sphere1[0], ['tx','tz','rx','ry','rz','sx','sy','sz','v'])
    lockHideAttr(sphere2[0], ['tx','tz','rx','ry','rz','sx','sy','sz','v'])
    lockHideAttr(circle1[0], ['tx','tz','rx','ry','rz','sx','sy','sz','v'])
    lockHideAttr(circle2[0], ['tx','tz','rx','ry','rz','sx','sy','sz','v'])
    lockHideAttr(loftedSurface[0], 'all')
    disableRenderStats(sphere1[0])
    disableRenderStats(sphere2[0])
    disableRenderStats(loftedSurface[0])

    # md node
    md1 = cmds.createNode('multiplyDivide')
    md2 = cmds.createNode('multiplyDivide')
    cmds.setAttr(md1 + ".operation", 1)
    cmds.setAttr(md1 + ".input2X", 0.5)
    cmds.setAttr(md2 + ".operation", 1)
    cmds.setAttr(md2 + ".input2X", -0.5)
    
    # connectAttr
    cmds.connectAttr(root + '.worldInverseMatrix[0]', loftedSurface[0] + '.offsetParentMatrix', f=True)

    cmds.connectAttr("{}.message".format(sphere1[0]), "{}.{}".format(root, 'sphereA'))
    cmds.connectAttr("{}.message".format(sphere2[0]), "{}.{}".format(root, 'sphereB'))
    cmds.connectAttr("{}.message".format(circle1[0]), "{}.{}".format(root, 'circleA'))
    cmds.connectAttr("{}.message".format(circle2[0]), "{}.{}".format(root, 'circleB'))
    cmds.connectAttr("{}.message".format(loftedSurface[0]), "{}.{}".format(root, 'loftedSurface'))

    cmds.connectAttr(md1 + '.outputX', sphere1[0] + '.ty', f=True)
    cmds.connectAttr(md2 + '.outputX', sphere2[0] + '.ty', f=True)
    cmds.connectAttr(md1 + '.outputX', circle1[0] + '.ty', f=True)
    cmds.connectAttr(md2 + '.outputX', circle2[0] + '.ty', f=True)
    
    cmds.connectAttr(root + '.height', md1 + '.input1X', f=True)
    cmds.connectAttr(root + '.height', md2 + '.input1X', f=True)
    cmds.connectAttr(root + '.radiusA', sphere1[1] + '.radius', f=True)
    cmds.connectAttr(root + '.radiusB', sphere2[1] + '.radius', f=True)
    cmds.connectAttr(root + '.radiusA', circle1[1] + '.radius', f=True)
    cmds.connectAttr(root + '.radiusB', circle2[1] + '.radius', f=True)
    cmds.connectAttr(root + '.displayType', sphere1[0] + '.overrideDisplayType', f=True)
    cmds.connectAttr(root + '.displayType', sphere2[0] + '.overrideDisplayType', f=True)
    cmds.connectAttr(root + '.displayType', loftedSurface[0] + '.overrideDisplayType', f=True)

    return root

@undoWrapper
def cuboid(*args):
    root, makePolyCube = cmds.polyCube(w=1, h=1, d=1, sx=1, sy=1, sz=1, ax=[0,1,0], n=getUniqueName('cuboidCollider'))
    lockHideAttr(root, ['sx','sy','sz'])
    addCommonAttr(root, 'cuboid')
    cmds.addAttr(root, ln='width', nn='Width', at='double', dv=1, min=0.001, k=True)
    cmds.addAttr(root, ln='height', nn='Height', at='double', dv=1, min=0.001, k=True)
    cmds.addAttr(root, ln='depth', nn='Depth', at='double', dv=1, min=0.001, k=True)
    setOutlinerColor(root, [1,1,0])
    disableRenderStats(root)

    # connectAttr
    cmds.connectAttr(root + '.width', makePolyCube + '.width', f=True)
    cmds.connectAttr(root + '.height', makePolyCube + '.height', f=True)
    cmds.connectAttr(root + '.depth', makePolyCube + '.depth', f=True)
    sh = cmds.listRelatives(root, s=True)[0]
    setOverrideColor(sh, 17)
    cmds.connectAttr(root + '.displayType', sh + '.overrideDisplayType', f=True)

    return root


def addCommonAttr(obj, colliderType, *args):
    cmds.addAttr(obj, ln='colliderType', nn='Collider Type', dt='string', k=False)
    cmds.setAttr(obj + '.colliderType', colliderType, type='string')
    cmds.addAttr(obj, ln='displayType', nn='Display Type', at='enum', en='Normal:Template:Reference', dv=0, k=True)
    for arg in args:
        cmds.addAttr(obj, ln=arg, at="message")