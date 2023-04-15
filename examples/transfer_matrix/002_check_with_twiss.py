import numpy as np

import xtrack as xt
import xpart as xp

# TODO try to go to kick drift in longitudinal and see if chrmaticity and
# dispersion accuracy is improved when goig to larger synchrotron tunes

x_co = [1e-3, 2e-3]
px_co = [2e-6, -3e-6]
y_co = [3e-3, 4e-3]
py_co = [4e-6, -5e-6]
betx = [1., 2.]
bety = [3., 4.]
alfx = [0, 0.1]
alfy = [0.2, 0.]
dx = [10, 0]
dy = [0, 20]
dpx = [0.7, -0.3]
dpy = [0.4, -0.6]
beta_s = 1e-3

segm_1 = xt.LinearTransferMatrix(Q_x=0.4, Q_y=0.3, Q_s=0.0001, 
                                 beta_s = beta_s, length=0.1,
                                 beta_x_0=betx[0], beta_x_1=betx[1],
                                 beta_y_0=bety[0], beta_y_1=bety[1],
                                 alpha_x_0=alfx[0], alpha_x_1=alfx[1],
                                 alpha_y_0=alfy[0], alpha_y_1=alfy[1],
                                 disp_x_0=dx[0], disp_x_1=dx[1],
                                 disp_px_0=dpx[0], disp_px_1=dpx[1],
                                 disp_y_0=dy[0], disp_y_1=dy[1],
                                 disp_py_0=dpy[0], disp_py_1=dpy[1],
                                 x_ref_0=x_co[0], x_ref_1=x_co[1],
                                 px_ref_0=px_co[0], px_ref_1=px_co[1],
                                 y_ref_0=y_co[0], y_ref_1=y_co[1],
                                 py_ref_0=py_co[0], py_ref_1=py_co[1])
segm_2 = xt.LinearTransferMatrix(Q_x=0.21, Q_y=0.32, Q_s=0.0003,
                                 beta_s = beta_s, length=0.2,
                                 chroma_x=2., chroma_y=3.,
                                 beta_x_0=betx[1], beta_x_1=betx[0],
                                 beta_y_0=bety[1], beta_y_1=bety[0],
                                 alpha_x_0=alfx[1], alpha_x_1=alfx[0],
                                 alpha_y_0=alfy[1], alpha_y_1=alfy[0],
                                 disp_x_0=dx[1], disp_x_1=dx[0],
                                 disp_px_0=dpx[1], disp_px_1=dpx[0],
                                 disp_y_0=dy[1], disp_y_1=dy[0],
                                 disp_py_0=dpy[1], disp_py_1=dpy[0],
                                 x_ref_0=x_co[1], x_ref_1=x_co[0],
                                 px_ref_0=px_co[1], px_ref_1=px_co[0],
                                 y_ref_0=y_co[1], y_ref_1=y_co[0],
                                 py_ref_0=py_co[1], py_ref_1=py_co[0])

line = xt.Line(elements=[segm_1, segm_2], particle_ref=xp.Particles(p0c=1e9))
line.build_tracker()

tw4d = line.twiss(method='4d')
tw6d = line.twiss()

assert np.isclose(tw6d.qs, 0.0004, atol=1e-7, rtol=0)
assert np.isclose(tw6d.betz0, 1e-3, atol=1e-7, rtol=0)

for tw in [tw4d, tw6d]:

    assert np.isclose(tw.qx, 0.4 + 0.21, atol=1e-7, rtol=0)
    assert np.isclose(tw.qy, 0.3 + 0.32, atol=1e-7, rtol=0)

    assert np.isclose(tw.dqx, 2, atol=1e-3, rtol=0)
    assert np.isclose(tw.dqy, 3, atol=1e-3, rtol=0)

    assert np.allclose(tw.s, [0, 0.1, 0.1 + 0.2], atol=1e-7, rtol=0)
    assert np.allclose(tw.mux, [0, 0.4, 0.4 + 0.21], atol=1e-7, rtol=0)
    assert np.allclose(tw.muy, [0, 0.3, 0.3 + 0.32], atol=1e-7, rtol=0)

    assert np.allclose(tw.betx, [1, 2, 1], atol=1e-7, rtol=0)
    assert np.allclose(tw.bety, [3, 4, 3], atol=1e-7, rtol=0)

    assert np.allclose(tw.alfx, [0, 0.1, 0], atol=1e-7, rtol=0)
    assert np.allclose(tw.alfy, [0.2, 0, 0.2], atol=1e-7, rtol=0)

    assert np.allclose(tw.dx, [10, 0, 10], atol=1e-4, rtol=0)
    assert np.allclose(tw.dy, [0, 20, 0], atol=1e-4, rtol=0)
    assert np.allclose(tw.dpx, [0.7, -0.3, 0.7], atol=1e-5, rtol=0)
    assert np.allclose(tw.dpy, [0.4, -0.6, 0.4], atol=1e-5, rtol=0)

    assert np.allclose(tw.x, [1e-3, 2e-3, 1e-3], atol=1e-7, rtol=0)
    assert np.allclose(tw.px, [2e-6, -3e-6, 2e-6], atol=1e-12, rtol=0)
    assert np.allclose(tw.y, [3e-3, 4e-3, 3e-3], atol=1e-7, rtol=0)
    assert np.allclose(tw.py, [4e-6, -5e-6, 4e-6], atol=1e-12, rtol=0)