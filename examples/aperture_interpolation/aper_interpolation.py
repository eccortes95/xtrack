import numpy as np
from scipy.spatial import ConvexHull

import xtrack as xt
import xline as xl

def interp_aperture(context, tracker, backtracker, i_aper_0, i_aper_1,
                       n_theta, r_max, dr, ds, _trk_gen):

    temp_buf = context.new_buffer()

    polygon_1, i_start_thin_1 = characterize_aperture(tracker,
                                 i_aper_1, n_theta, r_max, dr,
                                 buffer_for_poly=temp_buf)
    num_elements = len(tracker.line.elements)
    polygon_0, i_start_thin_0_bktr = characterize_aperture(backtracker,
                                 num_elements-i_aper_0-1,
                                 n_theta, r_max, dr,
                                 buffer_for_poly=temp_buf)
    i_start_thin_0 = num_elements - i_start_thin_0_bktr - 1

    s0 = tracker.line.element_s_locations[i_aper_0]
    s1 = tracker.line.element_s_locations[i_aper_1]

    # Interpolate

    Delta_s = s1 - s0

    s_vect = np.arange(s0, s1, ds)

    interp_polygons = []
    for ss in s_vect:
        x_non_convex=(polygon_1.x_vertices*(ss - s0) / Delta_s
                  + polygon_0.x_vertices*(s1 - ss) / Delta_s)
        y_non_convex=(polygon_1.y_vertices*(ss - s0) / Delta_s
                  + polygon_0.y_vertices*(s1 - ss) / Delta_s)
        hull = ConvexHull(np.array([x_non_convex, y_non_convex]).T)
        i_hull = np.sort(hull.vertices)
        x_hull = x_non_convex[i_hull]
        y_hull = y_non_convex[i_hull]
        interp_polygons.append(xt.LimitPolygon(
            _buffer=temp_buf,
            x_vertices=x_hull,
            y_vertices=y_hull))

    # Build interp line
    s_elements = [s0] + list(s_vect) +[s1]
    elements = [polygon_0] + interp_polygons + [polygon_1]

    for i_ele in range(i_start_thin_0+1, i_start_thin_1):
        ee = tracker.line.elements[i_ele]
        if not ee.__class__.__name__.startswith('Drift'):
            assert not hasattr(ee, 'isthick') or not ee.isthick
            ss_ee = tracker.line.element_s_locations[i_ele]
            elements.append(ee.copy(_buffer=temp_buf))
            s_elements.append(ss_ee)
    i_sorted = np.argsort(s_elements)
    s_sorted = list(np.take(s_elements, i_sorted))
    ele_sorted = list(np.take(elements, i_sorted))

    s_all = [s_sorted[0]]
    ele_all = [ele_sorted[0]]

    for ii in range(1, len(s_sorted)):
        ss = s_sorted[ii]

        if ss-s_all[-1]>1e-14:
            ele_all.append(xt.Drift(_buffer=temp_buf, length=ss-s_all[-1]))
            s_all.append(ss)
        ele_all.append(ele_sorted[ii])
        s_all.append(s_sorted[ii])


    interp_tracker = xt.Tracker(
            _buffer=temp_buf,
            sequence=xl.Line(elements=ele_all),
            track_kernel=_trk_gen.track_kernel,
            element_classes=_trk_gen.element_classes)

    return interp_tracker, i_start_thin_0, i_start_thin_1, s0, s1

def characterize_aperture(tracker, i_aperture, n_theta, r_max, dr,
                          buffer_for_poly):

    # find previous drift
    ii=i_aperture
    found = False
    while not(found):
        ccnn = tracker.line.elements[ii].__class__.__name__
        #print(ccnn)
        if ccnn == 'Drift':
            found = True
        else:
            ii -= 1
    i_start = ii + 1
    num_elements = i_aperture-i_start+1

    # Get polygon

    theta_vect = np.linspace(0, 2*np.pi, n_theta+1)[:-1]

    this_rmin = 0
    this_rmax = r_max
    this_dr = (this_rmax-this_rmin)/100.
    rmin_theta = 0*theta_vect
    t_iter = []
    for iteration in range(2):

        r_vect = np.arange(this_rmin, this_rmax, this_dr)

        RR, TT = np.meshgrid(r_vect, theta_vect)
        RR += np.atleast_2d(rmin_theta).T

        x_test = RR.flatten()*np.cos(TT.flatten())
        y_test = RR.flatten()*np.sin(TT.flatten())

        print(f'{iteration=} num_part={x_test.shape[0]}')

        ptest = xt.Particles(p0c=1,
                x = x_test.copy(),
                y = y_test.copy())
        tracker.track(ptest, ele_start=i_start, num_elements=num_elements)

        indx_sorted = np.argsort(ptest.particle_id)
        state_sorted = np.take(ptest.state, indx_sorted)

        state_mat = state_sorted.reshape(RR.shape)

        i_r_aper = np.argmin(state_mat>0, axis=1)

        rmin_theta = r_vect[i_r_aper-1]
        this_rmin=0
        this_rmax=2*this_dr
        this_dr = dr

    x_mat = x_test.reshape(RR.shape)
    y_mat = y_test.reshape(RR.shape)
    x_non_convex = np.array(
            [x_mat[itt, i_r_aper[itt]] for itt in range(n_theta)])
    y_non_convex = np.array(
            [y_mat[itt, i_r_aper[itt]] for itt in range(n_theta)])

    hull = ConvexHull(np.array([x_non_convex, y_non_convex]).T)
    i_hull = np.sort(hull.vertices)
    x_hull = x_non_convex[i_hull]
    y_hull = y_non_convex[i_hull]

    # Get a convex polygon that does not have points for all angles
    temp_poly = xt.LimitPolygon(x_vertices=x_hull, y_vertices=y_hull)

    # Get a convex polygon that has vertices at all requested angles
    r_out = 1. # m
    res = temp_poly.impact_point_and_normal(
            x_in=0*theta_vect, y_in=0*theta_vect, z_in=0*theta_vect,
            x_out=r_out*np.cos(theta_vect),
            y_out=r_out*np.sin(theta_vect),
            z_out=0*theta_vect)

    polygon = xt.LimitPolygon(x_vertices=res[0], y_vertices=res[1],
                              _buffer=buffer_for_poly)

    return polygon, i_start

