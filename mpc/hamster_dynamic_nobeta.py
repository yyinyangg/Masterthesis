import casadi as ca
import pandas as pd
import types
import os

Script_Root = os.path.abspath(os.path.dirname(__file__))

deg2R = lambda x: ca.pi*(x/180)


def load_path(path_file_name):
    df = pd.read_csv(os.path.join(Script_Root,"DATA", path_file_name, "path.csv"))
    s = df["s"].values
    curvature = df['curvature'].values
    interpolator = ca.interpolant("kappa_at_s", "bspline", [s], curvature)
    return interpolator, len(s), s[-1]

def get_hamster_model(path_file_name='circle'):
    interpolator, steps_length, path_length = load_path(path_file_name)
    model = types.SimpleNamespace()
    # model.mass = 1.5  # kg
    model.length_front = 0.125  # m
    model.length_rear = 0.125  # m
    model.steer_k1 = 2.25
    model.steer_k2 = 4
    model.L= model.length_rear + model.length_front
    model.T = 0.00984

    def dynamic_f(x, u, kappa):
        s, n, alpha, v = x[0], x[1], x[2], x[3]
        v_command, delta = u[0], u[1]

        # delta = ca.arctan(model.steer_k1*L*ca.tanh(model.steer_k2*delta))
        delta = model.steer_k1 * model.L * ca.tanh(model.steer_k2 * delta)

        s_dot = v*ca.cos(alpha)/(1-n*kappa)
        n_dot = v*ca.sin(alpha)
        alpha_dot = v*(ca.tan(delta)/model.L) - kappa*s_dot
        v_dot = (v_command-v)/model.T
        return ca.vertcat(s_dot, n_dot, alpha_dot, v_dot)

    # state vector
    s = ca.MX.sym("s")
    n = ca.MX.sym("n")
    alpha = ca.MX.sym("alpha")
    v = ca.MX.sym("v")
    x = ca.vertcat(s, n, alpha, v)
    kappa = ca.MX.sym("kappa")

    # control vector
    v_comm = ca.MX.sym("v_comm")
    delta = ca.MX.sym("delta")
    u = ca.vertcat(v_comm, delta)

    rhs = dynamic_f(x, u, kappa)
    model.dynamic = ca.Function("dynamic", [x,u, kappa], [rhs])

    constraints = types.SimpleNamespace()
    constraints.s_limit = path_length  # total curve length
    constraints.n_limit = ca.inf  # distance bias
    constraints.alpha_limit = ca.inf
    constraints.v_limit = 1#0.6  # m/
    constraints.v_comm_limit = 1# 0.6
    constraints.targ_vel = 0.5
    constraints.delta_limit = deg2R(28)  # 30 degree


    return model, constraints