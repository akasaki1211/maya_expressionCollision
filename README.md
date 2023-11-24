# Overview
![Maya](https://img.shields.io/static/v1?message=Maya&color=0696D7&logo=Autodesk&logoColor=white&label=) ![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)  

Create collision detection using expression node.  
It is created only with expression node of Maya standard function. No plug-in node or other installation is required.  

> **Supported :**  
> * Maya 2024 (Python3.10.8)  
> * Maya 2023 (Python3.9.7)  
> * Maya 2022 (Python3.7.7)  
> * Maya 2020 (Python2.7.11)  
> * Maya 2019 and below are **"not"** supported

Example of capsule collider :  
![Example of capsule collider](images/capsuleCollider.gif)  

# Supported colliders
![Supported colliders](images/colliders.png)  
* Infinite Plane
* Sphere
* Capsule
* Capsule2 (radius individually)
* Cuboid

# Installation
Please do one of the following:
* Copy the expcol directory into the `C:\Users\<username>\Documents\maya\scripts`.
* Add the parent directory of expcol to PYTHONPATH environment variable.
* Add the parent directory of expcol to PYTHONPATH in Maya.env.

> **Note**  
> `expcol` module is required on rigging, but is not needed on animation.

# Usage
## Create Collider
```python
from expcol import collider

collider.iplane()   # Infinite Plane
collider.sphere()   # Sphere
collider.capsule()  # Capsule
collider.capsule2() # Capsule2 (radius individually)
collider.cuboid()   # Cuboid
```

## Create Detection
```python
from expcol import detection

detection.create(
    'input', 
    'output', 
    'controller', 
    parent='parent', 
    colliders=collider_list, 
    groundCol=True, 
    scalable=False,
    radius_rate=None,
)
```
||||
|---|---|---|
|`input`|str|Child 'transform' or 'joint' before correction.|
|`output`|str|Child 'transform' or 'joint' after correction.|
|`controller`|str|Any node to add attributes for control.|
|`parent`|str, optional|Parent 'transform' or 'joint'.|
|`colliders`|list, optional|List of collider names. Defaults to [].|
|`groundCol`|bool, optional|Add horizontal plane collision. Defaults to False.|
|`scalable`|bool, optional|Allow for parent scale of joint-chain and parent scale of colliders. Defaults to False.|
|`radius_rate`|float, optional|Rate at which radius and tip radius are interpolated, between 0 and 1. Defaults to None.|

> **Note**  
> For more information on `input`, `output` and `parent`, please click [here](#what-are-input-output-and-parent).  

If you just want to add an attribute to a controller, do the following. It is also called in `detection.create`.  
```python
detection.add_control_attr(
    'controller', 
    groundCol=True, 
    tip_radius=True
)
```

## Example
Running the following code will create a sample joint, create a collider, and even create a detection.  
```python
from maya import cmds
from expcol import collider, detection

# Create sample joint chain
rootCtl = cmds.createNode('transform', n='rootCtl')
jointList = []
for i in range(5):
    jointList.append(cmds.joint(n='joint_{}'.format(i), p=[i*3,0,0]))
cmds.setAttr(rootCtl+'.ty', 5)

for i in range(len(jointList)-1):
    p = cmds.listRelatives(jointList[i], p=True)[0]
    pos1 = cmds.xform(jointList[i], q=True, ws=True, t=True)
    pos2 = cmds.xform(jointList[i+1], q=True, ws=True, t=True)
    prt = cmds.createNode('transform', n='parent_{}'.format(i), p=p)
    ipt = cmds.createNode('transform', n='input_{}'.format(i), p=p)
    out = cmds.createNode('transform', n='output_{}'.format(i), p=p)
    cmds.xform(prt, ws=True, t=pos1)
    cmds.xform(ipt, ws=True, t=pos2)
    cmds.xform(out, ws=True, t=pos2)
    cmds.aimConstraint(out, jointList[i], u=[0,0,1], wu=[0,0,1], wut='objectrotation', wuo=prt)

# Create Colliders
collider_list = []
collider_list.append(collider.iplane())
collider_list.append(collider.capsule())

# Create Detections
for i in range(len(jointList)-1):
    detection.create(
        'input_{}'.format(i), 
        'output_{}'.format(i), 
        'rootCtl', 
        parent='parent_{}'.format(i), 
        colliders=collider_list, 
        groundCol=True, 
        scalable=True,
        radius_rate=float(i)/float(len(jointList)-2)
    )
```

## `groundCol` option
Setting groundCol to True adds an invisible horizontal collision. The height can be changed with the GroundHeight value.  
![use_groundCol.gif](images/use_groundCol.gif)

## `scalable` option
If scalable is set to True, the scale of the parent of the joint-chain or the parent of the collider is reflected.  
|scalable=True|scalable=False|
|---|---|
|![scalable_true.gif](images/scalable_true.gif)|![scalable_false.gif](images/scalable_false.gif)|

## `radius_rate` option
Interpolate radius and tip_radius by the radius_rate value. 0.0 matches radius and 1.0 matches tip_radius.  
![radius_rate.png](images/radius_rate.png)

## `parent` option
When creating a detection for bone with length, `parent` option is usually used.  
If parent is not specified, a simple point detection is created.  
![no_parent.gif](images/no_parent.gif)

### example
```python
from maya import cmds
from expcol import collider, detection

# Create input and output
rootCtl = cmds.createNode('transform', n='rootCtl')
in_point = cmds.createNode('transform', n='input')
out_point = cmds.createNode('transform', n='output')
cmds.parent(in_point, rootCtl)
cmds.parent(out_point, rootCtl)
cmds.setAttr(rootCtl + '.ty', 5)

# Create Colliders
collider_list = []
collider_list.append(collider.sphere())
collider_list.append(collider.capsule())

# Create Detection
detection.create(
    in_point, 
    out_point, 
    rootCtl, 
    colliders=collider_list, 
    groundCol=True, 
    scalable=True
)
```

# What are Input, Output, and Parent?

|||
|---|---|
|Input|world position of the child joint before correction.|
|Output|world position of the child joint after correction.|
|Parent|world position of the parent joint.|

Each is just transform node, and there is no input connection to translate of Parent and Input.  
![ex_01.gif](images/explanation_of_parent_input_output/ex_01.gif)

Also, joint chain is not directly related to collision. It will be controlled by aim constraint or IK later.  
![ex_02.png](images/explanation_of_parent_input_output/ex_02.png)

If you have more than two joint chain, create the same node graph in the child hierarchy.  
It's the same for all patterns like Capsule, Infinite plane, Sphere...  
![ex_03.gif](images/explanation_of_parent_input_output/ex_03.gif)

# Note
* A high `Colision Iteration` value increases the accuracy of collision detection, but it also increases the processing load.
* A large number of detections can be very heavy.
* The number of colliders cannot be changed after a detection (expression node) is created.

## Processing time
Processing time per joint measured using maya's profiler.  
|Collider (Iteration:5)|Avg|
|---|---|
|sphere|32.57 us|
|iplane|33.70 us|
|capsule|39.27 us|
|capsule2|48.94 us|
|cuboid|50.30 us|

> * Windows 11  
> * Intel(R) Core(TM) i7-10700 CPU @ 2.90GHz  
> * Maya 2024  
