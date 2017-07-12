import numpy as np
from numpy.linalg import cholesky
from scipy.linalg import solve_triangular


def initialize(cTb, dim_c, dim_b):
    """ Initialize variables """

    f = [set([]) for i in range(dim_b[1])]
    g = [set(range(dim_c[1])) for i in range(dim_b[1])]

    x = np.zeros((dim_c[1], dim_b[1]))
    y = -cTb

    alpha = [3 for i in range(dim_b[1])]
    beta = [(dim_c[1] + 1) for i in range(dim_b[1])]

    return f, g, x, y, alpha, beta


def check_feasibility(x, y):
    """ checks whether or not any entry in x, y is negative and returns those indices """

    I = set()
    V = []
    for j in range(x.shape[1]):
        if np.any(x[:, j] < 0) or np.any(y[:, j] < 0):
            I.add(j)
            x_index_set = set([i for i, val in enumerate(x[:, j] < 0) if val])
            y_index_set = set([i for i, val in enumerate(y[:, j] < 0) if val])
            V.append(x_index_set.union(y_index_set))

    return I, V


def update_f_g(f, g, I, V, alpha, beta):
    """ update index sets F and G

    1. ideally exchange all infeasible indices
    2. exchange all infeasible indices at most 3 times if number of infeasible indices
        is not decreasing
    3. if number of indices does not increase, exchange only the biggest index

    """

    V_hat = []
    for j in I:
        if len(V[j]) < beta[j]:
            beta[j] = np.sum(V[j])
            alpha[j] = 3
            V_hat.append(V[j])
        elif len(V[j]) >= beta[j] and alpha[j] >= 1:
            alpha[j] -= 1
            V_hat.append(V[j])
        elif len(V[j]) >= beta[j] and alpha[j] == 0:
            V_hat.append(max(V[j]))
        else:
            raise Exception

        f[j] = (f[j] - V_hat[j]).union(V_hat[j].intersection(g[j]))
        g[j] = (g[j] - V_hat[j]).union(V_hat[j].intersection(f[j]))

    return f, g


def column_grouping(I, f, g, x, y, cTc, cTb):
    """ solves x_f, y_g for indexsets f, g

    The general alogrithm works as follows:
        1. take the set of infeasible indices I
        2. take the smallest index in I and look for all equal indexsets F
        3. take all indices of I that have the same indexset F and
            solve for x for this group (only one Cholesky decomp necessary)
        4. compute y for all relevant indices by substituting
        5. remove all picked indices from the I and repeat
            
    """

    not_picked = I.copy()
    picked = set([])
    while len(not_picked) > 0:
        # take minimal index of I and find all equal indexsets f
        current_min_index = min(not_picked)
        template = f[current_min_index]
        for index in not_picked:
            if template == f[index]:
                picked.add(index)

        # reduce cTc/cTb to relevant entries
        c_ixgrid = np.ix_(list(template), list(template))
        x_ixgrid = np.ix_(list(template), list(picked))

        x[x_ixgrid] = solve_for_x(cTc[c_ixgrid], cTb[list(template)])
        
        # compute all y's
        for index in picked:
            c_ixgrid = np.ix_(list(g[index]), list(f[index]))
            y_ixgrid = np.ix_(list(g[index]))

            y[y_ixgrid, index] = solve_for_y(cTc[c_ixgrid], cTb[list(g[index]), index], x[:, index])

        # remove computed indices
        not_picked -= picked
        picked = set([])

    return x, y


def solve_for_x(A, B):
    """ solve normal equation via Cholesky decomposition and
    forward/backward substitution """
    L = cholesky(A)
    x = np.zeros(B.shape)
    for i in range(B.shape[1]):
        y = solve_triangular(L, B[:, i], lower=True)
        x[:, i] = solve_triangular(L, y, lower=True, trans=1)
    return x


def solve_for_y(A, B, x):
    """ """
    return A @ x - B


def check_convergence():
    """ """
    if True:
        return True
    else:
        return False


def bpp(c, b):
    """ Block principal pivoting algorithm

    solves the NNLS problem:

        min_(x>0) || CX - B ||_F^2

    """

    # precompute matrices
    cTc = c.T @ c
    cTb = c.T @ b

    # initialize variables
    f, g, x, y, alpha, beta = initialize(cTb, c.shape, b.shape)

    # iterate until x, y are feasable
    infeasible = True
    convergence = False
    while infeasible and not convergence:
        
        infeasible_indices, infeasible_var = check_feasibility(x, y) 

        f, g = update_f_g(f, g, infeasible_indices, infeasible_var, alpha, beta)

        # calc x by column grouping
        x, y = column_grouping(infeasible_indices, f, g, x, y, cTc, cTb)

        convergence = check_convergence()

    return x
