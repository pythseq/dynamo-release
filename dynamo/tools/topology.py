# create by Yan Zhang, minor adjusted by Xiaojie Qiu

import numpy as np
from scipy.optimize import fsolve
from scipy.spatial.distance import pdist
from scipy.linalg import eig
from scipy.integrate import odeint
from .scVectorField import con_K

def vector_field_function(x, VecFld, dim=None):
    """Learn an analytical function of vector field from sparse single cell samples on the entire space robustly.
    Reference: Regularized vector field learning with sparse approximation for mismatch removal, Ma, Jiayi, etc. al, Pattern Recognition
    """
    # x=np.array(x).reshape((1, -1))
    x = np.array(x)
    if (x.ndim == 1):
        x = x[None, :]
    K = con_K(x, VecFld['X'], VecFld['beta'])

    if dim is None:
        K = K.dot(VecFld['C'])
    else:
        K = K.dot(VecFld['C'][:, dim])
    return K


def index_condensed_matrix(n, i, j):
    """Return the index of a condensed n-by-n square matrix by the row index i and column index j of the square form.

    Arguments
    ---------
        n: int
            Size of the squareform.
        i: int
            Row index of the element in the squareform.
        j: int
            Column index of the element in the the squareform.

    Returns
    -------
        k: int
            The index of the element in the condensed matrix.
    """
    return int(i * (n - (i + 3) * 0.5) + j - 1)


def remove_redundant_points(X, tol=1e-4, output_discard=False):
    X = np.atleast_2d(X)
    discard = np.zeros(len(X), dtype=bool)
    if X.shape[0] > 1:
        dist = pdist(X)
        for i in range(len(X)):
            for j in range(i + 1, len(X)):
                if dist[index_condensed_matrix(len(X), i, j)] < tol:
                    discard[j] = True
        X = X[~discard]
    if output_discard:
        return X, discard
    else:
        return X


def find_fixed_points(X0, func_vf, tol_redundant=1e-4, full_output=False):
    X = []
    J = []
    fval = []
    for x0 in X0:
        if full_output:
            x, info_dict, _, _ = fsolve(func_vf, x0, full_output=True)
            fval.append(info_dict['fvec'])
            # compute Jacobian
            Q = info_dict['fjac']
            R = form_triu_matrix(info_dict['r'])
            J.append(Q.T @ R)
        else:
            x = fsolve(func_vf, x0)
        X.append(x)
    X = np.array(X)
    if full_output:
        J = np.array(J)
        fval = np.array(fval)

    if tol_redundant is not None:
        if full_output:
            X, discard = remove_redundant_points(X, tol_redundant, output_discard=True)
            J = J[~discard]
            fval = fval[~discard]
        else:
            X = remove_redundant_points(X, tol_redundant)

    if full_output:
        return X, J, fval
    else:
        return X


def pac_onestep(x0, func, v0, ds=0.01):
    x01 = x0 + v0 * ds
    F = lambda x: np.array([func(x), (x - x0).dot(v0) - ds])
    x1 = fsolve(F, x01)
    return x1


def continuation(x0, func, s_max, ds=0.01, v0=None, param_axis=0, param_direction=1):
    ret = [x0]
    if v0 is None:  # initialize tangent predictor
        v = np.zeros_like(x0)
        v[param_axis] = param_direction
    else:
        v = v0
    s = 0
    while (s <= s_max):
        x1 = ret[-1]
        x = pac_onestep(x1, func, v, ds)
        ret.append(x)
        s += ds

        # compute tangent predictor
        v = x - x1
        v /= np.linalg.norm(v)
    return np.array(ret)


def clip_curves(curves, domain, tol_discont=None):
    ret = []
    for cur in curves:
        clip_away = np.zeros(len(cur), dtype=bool)
        for i, p in enumerate(cur):
            for j in range(len(domain)):
                if p[j] < domain[j][0] or p[j] > domain[j][1]:
                    clip_away[i] = True
                    break
            if tol_discont is not None and i > 0:
                d = np.linalg.norm(p - cur[i - 1])
                if d > tol_discont:
                    clip_away[i] = True
        # clip curve and assemble
        i_start = 0
        while (i_start < len(cur) - 1):
            if not clip_away[i_start]:
                for i_end in range(i_start, len(cur)):
                    if clip_away[i_end]: break
                ret.append(cur[i_start: i_end])  # a tiny bit of the end could be chopped off
                i_start = i_end
            else:
                i_start += 1
    return ret


def compute_nullclines_2d(X0, fdx, fdy, x_range, y_range, s_max=None, ds=None):
    if s_max is None:
        s_max = 5 * ((x_range[1] - x_range[0]) + (y_range[1] - y_range[0]))
    if ds is None: ds = s_max / 1e3

    NCx = []
    NCy = []
    for x0 in X0:
        # initialize tangent predictor
        theta = np.random.rand() * 2 * np.pi
        v0 = [np.cos(theta), np.sin(theta)]
        v0 /= np.linalg.norm(v0)
        # nullcline continuation
        NCx.append(continuation(x0, fdx, s_max, ds, v0=v0))
        NCx.append(continuation(x0, fdx, s_max, ds, v0=-v0))
        NCy.append(continuation(x0, fdy, s_max, ds, v0=v0))
        NCy.append(continuation(x0, fdy, s_max, ds, v0=-v0))
    NCx = clip_curves(NCx, [x_range, y_range], ds * 10)
    NCy = clip_curves(NCy, [x_range, y_range], ds * 10)
    return NCx, NCy


def compute_separatrices(Xss, Js, func, x_range, y_range, t=50, n_sample=500, eps=1e-6):
    ret = []
    for i, x in enumerate(Xss):
        print(x)
        J = Js[i]
        w, v = eig(J)
        I_stable = np.where(np.real(w) < 0)[0]
        print(I_stable)
        for j in I_stable: # I_unstable
            u = np.real(v[j])
            u = u / np.linalg.norm(u)
            print('u=%f, %f' % (u[0], u[1]))

            # Parameters for building separatrix
            T = np.linspace(0, t, n_sample)
            # all_sep_a, all_sep_b = None, None
            # Build upper right branch of separatrix
            ab_upper = odeint(lambda x, _: -func(x), x + eps * u, T)
            # Build lower left branch of separatrix
            ab_lower = odeint(lambda x, _: -func(x), x - eps * u, T)

            sep = np.vstack((ab_lower[::-1], ab_upper))
            ret.append(sep)
    ret = clip_curves(ret, [x_range, y_range])
    return ret


def set_test_points_on_curve(curve, interval):
    P = [curve[0]]
    dist = 0
    for i in range(1, len(curve)):
        dist += np.linalg.norm(curve[i] - curve[i - 1])
        if dist >= interval:
            P.append(curve[i])
            dist = 0
    return np.array(P)


def find_intersection_2d(curve1, curve2, tol_redundant=1e-4):
    P = []
    for i in range(len(curve1) - 1):
        for j in range(len(curve2) - 1):
            p1 = curve1[i]
            p2 = curve1[i + 1]
            p3 = curve2[j]
            p4 = curve2[j + 1]
            denom = np.linalg.det([p1 - p2, p3 - p4])
            if denom != 0:
                t = np.linalg.det([p1 - p3, p3 - p4]) / denom
                u = -np.linalg.det([p1 - p2, p1 - p3]) / denom
                if t >= 0 and t <= 1 and u >= 0 and u <= 1:
                    P.append(p1 + t * (p2 - p1))
    if tol_redundant is not None:
        remove_redundant_points(P, tol=tol_redundant)
    return np.array(P)


def find_fixed_points_nullcline(func, NCx, NCy, sample_interval=0.5, tol_redundant=1e-4, full_output=False):
    test_Px = []
    for i in range(len(NCx)):
        test_Px.append(set_test_points_on_curve(NCx[i], sample_interval))

    test_Py = []
    for i in range(len(NCy)):
        test_Py.append(set_test_points_on_curve(NCy[i], sample_interval))

    int_P = []
    for i in range(len(test_Px)):
        for j in range(len(test_Py)):
            p = find_intersection_2d(test_Px[i], test_Py[j], tol_redundant)
            for k in range(len(p)):
                int_P.append(p[k])
    int_P = np.array(int_P)
    if full_output:
        P, J, _ = find_fixed_points(int_P, func, tol_redundant, full_output=True)
        return P, J
    else:
        P = find_fixed_points(int_P, func, tol_redundant)
        return P


def form_triu_matrix(arr):
    n = int(np.ceil((np.sqrt(1 + 8 * len(arr)) - 1) * 0.5))
    M = np.zeros((n, n))
    c = 0
    for i in range(n):
        for j in range(n):
            if j >= i:
                if c < len(arr):
                    M[i, j] = arr[c]
                    c += 1
                else:
                    break
    return M


def is_outside(X, domain):
    is_outside = np.zeros(X.shape[0], dtype=bool)
    for k in range(X.shape[1]):
        o = np.logical_or(X[:, k] < domain[k][0], X[:, k] > domain[k][1])
        is_outside = np.logical_or(is_outside, o)
    return is_outside


class FixedPoints:
    def __init__(self, X=None, J=None):
        self.X = X if X is not None else []
        self.J = J if J is not None else []
        self.eigvals = []

    def get_X(self):
        return np.array(self.X)

    def get_J(self):
        return np.array(self.J)

    def add_fixed_points(self, X, J, tol_redundant=1e-4):
        for i, x in enumerate(X):
            redundant = False
            if tol_redundant is not None and len(self.X) > 0:
                for y in self.X:
                    if np.linalg.norm(x - y) <= tol_redundant:
                        redundant = True
            if not redundant:
                self.X.append(x)
                self.J.append(J[i])

    def compute_eigvals(self):
        self.eigvals = []
        for i in range(len(self.J)):
            w, _ = eig(self.J[i])
            self.eigvals.append(w)

    def is_stable(self):
        if len(self.eigvals) != len(self.X):
            self.compute_eigvals()

        stable = np.ones(len(self.eigvals), dtype=bool)
        for i, w in enumerate(self.eigvals):
            if np.any(np.real(w) >= 0):
                stable[i] = False
        return stable

    def is_saddle(self):
        is_stable = self.is_stable()
        saddle = np.zeros(len(self.eigvals), dtype=bool)
        for i, w in enumerate(self.eigvals):
            if not is_stable[i] and np.any(np.real(w) < 0):
                saddle[i] = True
        return saddle, is_stable


class VectorField2D:
    def __init__(self, func, func_vx=None, func_vy=None):
        self.func = func

        def func_dim(x, func, dim):
            y = func(x)
            if y.ndim == 1:
                y = y[dim]
            else:
                y = y[:, dim].flatten()
            return y

        if func_vx is None:
            self.fx = lambda x: func_dim(x, self.func, 0)
        else:
            self.fx = func_vx
        if func_vy is None:
            self.fy = lambda x: func_dim(x, self.func, 1)
        else:
            self.fy = func_vy
        self.Xss = FixedPoints()
        self.NCx = None
        self.NCy = None

    def get_fixed_points(self, get_types=True):
        X = self.Xss.get_X()
        if not get_types:
            return X
        else:
            is_saddle, is_stable = self.Xss.is_saddle()
            # -1 -- stable, 0 -- saddle, 1 -- unstable
            ftype = np.ones(len(X))
            for i in range(len(ftype)):
                if is_saddle[i]:
                    ftype[i] = 0
                elif is_stable[i]:
                    ftype[i] = -1
            return X, ftype

    def find_fixed_points_by_sampling(self, n, x_range, y_range, lhs=True, tol_redundant=1e-4):
        if lhs:
            from .utils import lhsclassic
            X0 = lhsclassic(n, 2)
        else:
            X0 = np.random.rand(n, 2)
        X0[:, 0] = X0[:, 0] * (x_range[1] - x_range[0]) + x_range[0]
        X0[:, 1] = X0[:, 1] * (y_range[1] - y_range[0]) + y_range[0]
        X, J, _ = find_fixed_points(X0, self.func, tol_redundant=tol_redundant, full_output=True)
        # remove points that are outside the domain
        outside = is_outside(X, [x_range, y_range])
        self.Xss.add_fixed_points(X[~outside], J[~outside], tol_redundant)

    def find_nearest_fixed_point(self, x, x_range, y_range, tol_redundant=1e-4):
        X, J, _ = find_fixed_points(x, self.func, tol_redundant=tol_redundant, full_output=True)
        # remove point if outside the domain
        outside = is_outside(X, [x_range, y_range])[0]
        if not outside:
            self.Xss.add_fixed_points(X, J, tol_redundant)

    def compute_nullclines(self, x_range, y_range, find_new_fixed_points=False, tol_redundant=1e-4):
        # compute arguments
        s_max = 5 * ((x_range[1] - x_range[0]) + (y_range[1] - y_range[0]))
        ds = s_max / 1e3
        self.NCx, self.NCy = compute_nullclines_2d(self.Xss.get_X(), self.fx, self.fy, x_range, y_range, s_max=s_max,
                                                   ds=ds)
        if find_new_fixed_points:
            sample_interval = ds * 10
            X, J = find_fixed_points_nullcline(self.func, self.NCx, self.NCy, sample_interval, tol_redundant, True)
            outside = is_outside(X, [x_range, y_range])
            self.Xss.add_fixed_points(X[~outside], J[~outside], tol_redundant)

    def output_to_dict(self, dict_vf):
        dict_vf['NCx'] = self.NCx
        dict_vf['NCy'] = self.NCy
        dict_vf['Xss'] = self.Xss.get_X()
        dict_vf['J'] = self.Xss.get_J()
        return dict_vf
