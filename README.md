# Overview
Create collision detection using expression node.

It is created only with expression node of Maya standard function. No plug-in node or other installation is required.

**Tested with :**
* Maya 2024 (Python3.10.8)  
* Maya 2023 (Python3.9.7)  
* Maya 2022 (Python3.7.7)  
* Maya 2020 (Python2.7.11)  
* Maya 2019 and below are not supported

**Example of capsule collider :**
![Example of capsule collider](images/capsuleCollider.gif)  

# Supported colliders
![Supported colliders](images/colliders.jpg)  
* Infinite Plane
* Sphere
* Capsule
* Capsule2 (radius individually)

# Installation
Please do one of the following:
* Copy the expCol directory into the `C:\Users\<username>\Documents\maya\scripts`.
* Add the parent directory of expCol to PYTHONPATH environment variable.
* Add the parent directory of expCol to PYTHONPATH in Maya.env.

# Usage
## Create Collider
```python
from expCol import collider

collider.iplane()
collider.sphere()
collider.capsule()
collider.capsule2()
```

## Create Detection
```python
from expCol import detection

detection.create(
    'parent', 
    'input', 
    'output', 
    'controller', 
    colliders=collider_list, 
    groundCol=True, 
    scalable=False,
    radius_rate=None,
)
```
* parent : Parent 'transform'.  
* input : Child 'transform' before correction.  
* output : Child 'transform' after correction.   
  > For more information on parent, input and output, please click [here](https://twitter.com/akasaki1211/status/1489478989039108099).  
* controller : Any node to add attributes for control.  
* colliders : List of collider names.
* groundCol : Add horizontal plane collision. (*optional)
* scalable : Allow for parent scale of joint-chain and parent scale of colliders. (*optional)
* radius_rate : Rate at which radius and tip radius are interpolated, between 0 and 1.


## Example
```python
import maya.cmds as cmds
from expCol import collider, detection

# sample joint chain
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
    cmds.xform(prt, ws=1, t=pos1)
    cmds.xform(ipt, ws=1, t=pos2)
    cmds.xform(out, ws=1, t=pos2)
    cmds.aimConstraint(out, jointList[i], u=[0,0,1], wu=[0,0,1], wut='objectrotation', wuo=prt)

# Create Colliders
collider_list = []
collider_list.append(collider.iplane())
collider_list.append(collider.capsule())

# Create Detections
for i in range(len(jointList)-1):
    detection.create(
        'parent_{}'.format(i), 
        'input_{}'.format(i), 
        'output_{}'.format(i), 
        'rootCtl', 
        colliders=collider_list, 
        groundCol=True, 
        scalable=True,
        radius_rate=float(i)/float(len(jointList)-2)
    )
```

# Note
* A large number of detections can be very heavy.
* The number of colliders cannot be changed after a detection (expression node) is created.
