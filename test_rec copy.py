import numpy as np

dict_a = {'x': 0.010493925765318686, 'y': 0, 'z': 0}
b= np.array([dict_a['x'], dict_a['y'], dict_a['z']])
a = np.array(dict_a)
print(a)
print(type(a))
print(b)
print(type(b))