import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

Script_Root = os.path.abspath(os.path.dirname(__file__))

traj_name = "test_traj"
try:
    df = pd.read_csv(os.path.join(Script_Root, f"{traj_name}.csv"), sep=";",skiprows=2)
    data = df.iloc[0:,0:5]
    x_c, y_c = data[' x_m'].values, data[' y_m'].values

    # x_c, y_c = np.flip(x_c), np.flip(y_c)

    s_c = data['# s_m'].values
    start_index = 0
    x_c = np.hstack([x_c[start_index:], x_c[1:start_index+1]])
    y_c = np.hstack([y_c[start_index:], y_c[1:start_index+1]])
    s_c = np.hstack([s_c[start_index:]-s_c[start_index], s_c[1:start_index+1]+s_c[-1]-s_c[start_index]])

    x_padding = np.hstack([x_c[-3:-1], x_c, x_c[1:3]])
    y_padding = np.hstack([y_c[-3:-1], y_c, y_c[1:3]])
    dx = np.gradient(x_padding)
    dy = np.gradient(y_padding)
    ddx = np.gradient(dx)
    ddy = np.gradient(dy)

    psi = np.arctan2(dy, dx)
    curvature = -(ddx * dy - ddy * dx) / (dx ** 2 + dy ** 2) ** 1.5

    psi = psi[2:-2]
    curvature = curvature[2:-2]

    # regu_data = []
    # for idx in ['# s_m', ' x_m', ' y_m', ' kappa_radpm']:
    #     regu_data.append(data[idx].values)
    # for i in [' psi_rad']:
    #     trans = 0.5 * np.pi + data[i].values
        # temp = trans[-1]
        # trans[1:] = trans[0:-1]
        # trans[0] = temp
        # trans[trans > 2*np.pi] %= 2*np.pi
        # trans[trans < -2 * np.pi] %= -2 * np.pi
        # trans[trans > np.pi] -= 2*np.pi
        # trans[trans < -np.pi] += 2*np.pi
        # regu_data.append(trans)

    regu_data = [s_c, x_c, y_c, curvature, psi]
    regu_data = np.column_stack(regu_data)
    columns = ["s", 'x', 'y', 'curvature', 'psi_curve']
    data_save = pd.DataFrame(regu_data, columns=columns)
    if not os.path.exists(os.path.join(Script_Root, f'{traj_name}')):
        os.makedirs(os.path.join(Script_Root, f'{traj_name}'))
    data_save.to_csv(os.path.join(Script_Root, f'{traj_name}', 'path.csv'), index=False)


    x,y = data_save['x'].values, data_save['y'].values
    s, kappa = data_save['s'].values, data_save['curvature'].values

    norm = plt.Normalize(kappa.min(), kappa.max())
    cmap = plt.get_cmap('coolwarm')
    fig, ax = plt.subplots()
    for i in range(len(x) - 1):
        ax.plot(x[i:i + 2], y[i:i + 2], color=cmap(norm(kappa[i])))
    # plt.plot(x, y)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    plt.colorbar(sm, ax=ax, label='Curvature (kappa)')
    plt.title("test_traj")
    plt.xlabel("X (m)")
    plt.ylabel("Y (m)")
    plt.savefig(os.path.join(Script_Root, "test_traj", "path_plot.png"))
    plt.show()

    plt.plot(s, kappa)
    plt.xlabel('s (m)')
    plt.ylabel("curvature")
    plt.savefig(os.path.join(Script_Root, "test_traj", "param_path.png"))
    plt.show()

except FileNotFoundError:
    print(f"file {traj_name} not found ")
