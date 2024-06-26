from hamster_dynamic import get_casadi_model
import numpy as np
import casadi as ca
import pandas as pd
from typing import Optional
import time
import os

Script_Root = os.path.abspath(os.path.dirname(__file__))

class TIME_OPT_Traj:

    def __init__(self):
        self.model = get_casadi_model()
        self.dt: Optional[float] = 0.02  # Time step (second)
        self.N: Optional[int] = 250  # Prediction horizon
        self.nx: Optional[int] = 4
        self.nu: Optional[int] = 2
        self.path_root = os.path.join(Script_Root, 'DATA', 'path')
        self.path_list = os.listdir(self.path_root)
        self.U_opt: Optional[np.ndarray] = None
        self.X_opt: Optional[np.ndarray] = None

    def process_single_path(self, case_name='circle'):

        # load arc length and curvature
        df = pd.read_csv(os.path.join(self.path_root, case_name, 'path.csv'))
        s, kappa = list(df["s"].values), list(df["curvature"].values)

        # define state and control vector
        U = ca.MX.sym('U', self.nu, self.N)  # Input sequence
        X = ca.MX.zeros(self.nx, self.N +1)
        xf = ca.MX([s[-1], 0, 0, 0])
        x0 = ca.MX([0,0,0,0])
        X[:,0] = x0

        g = []
        lbg = []
        ubg = []

        # self.dt = 5/self.N

        for i in range(self.N):
            x_current, u_current = X[:, i], U[:, i]
            curvature = 0.5
            dx = self.model.dynamic(x=x_current, u=u_current, curvature=curvature)
            x_next = x_current + dx * self.dt
            X[:, i+1] = x_next

            # constrain positive s
            g.append(-X[0, i+1])
            lbg.append(-ca.inf)
            ubg.append(0)

            # constrain n
            g.append(X[1, i+1] - 1/curvature)
            lbg.extend([-ca.inf])
            ubg.extend([0])

            # constrain alpha
            rotation_tol = np.pi*0.25
            g.append(X[2, i+1] - rotation_tol)
            g.append(-rotation_tol - X[2, i+1])
            lbg.extend([-ca.inf]*2)
            ubg.extend([0]*2)

            # constrain velocity limit
            g.append(X[3, i+1] - self.model.velocity_limit)
            g.append(-self.model.velocity_limit - X[3, i+1])
            lbg.extend([-ca.inf]*2)
            ubg.extend([0]*2)

            # J += ca.norm_2(x_next - xf)**2
        J = ca.norm_2(X[:, -1] - xf)**2
        # terminal state constrain
        # g.append(state_history[-1] - xf)
        # lbg.extend([0]*self.nx)
        # ubg.extend([0]*self.nx)

        umax, umin = [self.model.velocity_limit, self.model.steering_limit], [-self.model.velocity_limit, -self.model.steering_limit]

        # g.append(U-ca.repmat(umax, self.N))
        # g.append(ca.repmat(umin, self.N) - U)
        # lbg.extend([-ca.inf]*2*self.nu*self.N)
        # ubg.extend([0]*2*self.nu*self.N)
        lbx = umin * self.N
        ubx = umax * self.N

        nlp = {'x':  ca.reshape(U, -1, 1), 'f': J, 'g': ca.vertcat(*g)}
        opts = {'ipopt.print_level': 0, 'print_time': 0, 'ipopt.tol': 1e-6}
        solver = ca.nlpsol('TOpt_solver', 'ipopt', nlp, opts)

        # Solve optimization problem
        start = time.time()
        res = solver(x0=ca.repmat(0, self.nu * self.N, 1), lbx=lbx, ubx=ubx, lbg=lbg, ubg=ubg)
        duration = time.time() - start
        print("Duration: ", duration)

        # constrain_value = res['g'].full()
        # print("terminal constrain value: ",constrain_value)

        # Extract optimal trajectory
        self.U_opt = ca.reshape(res['x'], self.nu, self.N).full()
        F = ca.Function('F', [U], [X])
        self.X_opt = F(self.U_opt).full()


if __name__ == "__main__":

    time_opt = TIME_OPT_Traj()
    time_opt.process_single_path()