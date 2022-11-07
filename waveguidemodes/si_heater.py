from collections import OrderedDict

import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon

from skfem import ElementTriP0, Basis, Mesh

from waveguidemodes.mesh import mesh_from_polygons
from waveguidemodes.thermal import solve_thermal

# Simulating the TiN TOPS heater in https://doi.org/10.1364/OE.27.010456

w_sim = 8 * 2
h_clad = 2.8
h_box = 2
w_core = 0.5
h_core = 0.22
w_buffer = .8
h_heater = h_buffer = .09
w_heater = 1
offset_heater = 2.2

polygons = OrderedDict(
    core=Polygon([
        (-w_core / 2, 0),
        (-w_core / 2, h_core),
        (w_core / 2, h_core),
        (w_core / 2, 0),
    ]),
    slab_l=Polygon([
        (-w_core / 2 - w_buffer, 0),
        (-w_core / 2 - w_buffer, h_heater),
        (-w_core / 2, h_heater),
        (-w_core / 2, 0),
    ]),
    slab_r=Polygon([
        (+w_core / 2 + w_buffer, 0),
        (+w_core / 2 + w_buffer, h_heater),
        (+w_core / 2, h_heater),
        (+w_core / 2, 0),
    ]),
    heater_l=Polygon([
        (-w_core / 2 - w_buffer - w_heater, 0),
        (-w_core / 2 - w_buffer - w_heater, h_heater),
        (-w_core / 2 - w_buffer, h_heater),
        (-w_core / 2 - w_buffer, 0),
    ]),
    heater_r=Polygon([
        (w_core / 2 + w_buffer + w_heater, 0),
        (w_core / 2 + w_buffer + w_heater, h_heater),
        (w_core / 2 + w_buffer, h_heater),
        (w_core / 2 + w_buffer, 0),
    ]),
    clad=Polygon([
        (-w_sim / 2, 0),
        (-w_sim / 2, h_clad),
        (w_sim / 2, h_clad),
        (w_sim / 2, 0),
    ]),
    box=Polygon([
        (-w_sim / 2, 0),
        (-w_sim / 2, - h_box),
        (w_sim / 2, - h_box),
        (w_sim / 2, 0),
    ])
)

resolutions = dict(
    core={"resolution": 0.001, "distance": 1},
    clad={"resolution": 0.4, "distance": 1},
    box={"resolution": 0.4, "distance": 1},
    heater_l={"resolution": 0.001, "distance": 1},
    heater_r={"resolution": 0.001, "distance": 1}
)

mesh_from_polygons(polygons, resolutions, filename='mesh.msh', default_resolution_max=.1)

mesh = Mesh.load('mesh.msh')

basis0 = Basis(mesh, ElementTriP0(), intorder=4)
thermal_conductivity_p0 = basis0.zeros()
for domain, value in {"core": 90, "box": 1.38, "clad": 1.38, "slab_l": 55, "slab_r": 55,
                      "heater_l": 55, "heater_r": 55}.items():
    thermal_conductivity_p0[basis0.get_dofs(elements=domain)] = value
thermal_conductivity_p0 *= 1e-12  # 1e-12 -> conversion from 1/m^2 -> 1/um^2

power = 25.2e-3
current = np.sqrt(power * 1e5 * (polygons['heater_l'].area + polygons['heater_r'].area) * 1e-12 / 320e-6)
print(current)
print(current / (polygons['heater_l'].area + polygons['heater_r'].area))

basis, temperature = solve_thermal(basis0, thermal_conductivity_p0,
                                   specific_conductivity={"heater_l": 1e5, "heater_r": 1e5},
                                   current_densities={
                                       "heater_l": current / (polygons['heater_l'].area + polygons['heater_r'].area),
                                       "heater_r": current / (polygons['heater_l'].area + polygons['heater_r'].area)
                                   })
basis.plot(temperature, colorbar=True)
plt.show()
