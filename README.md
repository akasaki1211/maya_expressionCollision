# Overview
Create collision detection using expression node.

It is created only with expression node of Maya standard function. No plug-in node or other installation is required.

**Tested with :**
* Maya 2020 (Python2.7)  
* Maya 2022 (Python3.7)  
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
* Copy the expCol folder into the `C:\Users\<username>\Documents\maya\scripts`.
* Add the parent directory of expCol to PYTHONPATH environment variable.
* Add the parent directory of expCol to PYTHONPATH in Maya.env.

# Usage
```
from expCol import collider, detection

# Create Collider
collider_list = []
collider_list.append(collider.iplane())
collider_list.append(collider.sphere())
collider_list.append(collider.capsule())
collider_list.append(collider.capsule2())

# Create Detection
detection.create('parent', 'input', 'output', 
                'controller', 
                colliders=collider_list, 
                groundCol=True)
```

# Note
* A large number of detections can be very heavy.
* The number of colliders cannot be changed after a detection (expression node) is created.
* Scale is not supported.
* [Explanation on twitter](https://twitter.com/akasaki1211/status/1489478989039108099)