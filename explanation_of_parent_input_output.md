# What are Parent, Input, and Output?"

|||
|---|---|
|Parent|world position of the parent joint.|
|Input|world position of the child joint before correction.|
|Output|world position of the child joint after correction.|

Each is just transform node, and there is no input connection to translate of Parent and Input.
![ex_01.gif](images/explanation_of_parent_input_output/ex_01.gif)

Also, joint chain is not directly related to collision. It will be controlled by aim constraint or IK later.
![ex_02.png](images/explanation_of_parent_input_output/ex_02.png)

If you have more than two joint chain, create the same node graph in the child hierarchy.  
It's the same for all patterns like Capsule, Infinite plane, Sphere...
![ex_03.gif](images/explanation_of_parent_input_output/ex_03.gif)