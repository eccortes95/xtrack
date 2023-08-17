import numpy as np
import xtrack as xt

from cpymad.madx import Madx

mad = Madx()
mad.call('fccee_h.seq')
mad.beam(particle='positron', pc=120)
mad.use('fccee_p_ring')
twm = mad.twiss()

line_thick = xt.Line.from_madx_sequence(mad.sequence.fccee_p_ring, allow_thick=True,
                                  deferred_expressions=True)
line_thick.particle_ref = xt.Particles(mass0=xt.PROTON_MASS_EV,
                                 gamma0=mad.sequence.fccee_p_ring.beam.gamma)
line_thick.build_tracker()
tw_thick_no_rad = line_thick.twiss()

line = line_thick.copy()
Strategy = xt.slicing.Strategy
Teapot = xt.slicing.Teapot
slicing_strategies = [
    Strategy(slicing=Teapot(1)),  # Default catch-all as in MAD-X
    Strategy(slicing=Teapot(3), element_type=xt.Bend),
    Strategy(slicing=Teapot(3), element_type=xt.CombinedFunctionMagnet),
    # Strategy(slicing=Teapot(50), element_type=xt.Quadrupole), # Starting point
    Strategy(slicing=Teapot(5), name=r'^qf.*'),
    Strategy(slicing=Teapot(5), name=r'^qd.*'),
    Strategy(slicing=Teapot(5), name=r'^qfg.*'),
    Strategy(slicing=Teapot(5), name=r'^qdg.*'),
    Strategy(slicing=Teapot(5), name=r'^ql.*'),
    Strategy(slicing=Teapot(5), name=r'^qs.*'),
    Strategy(slicing=Teapot(10), name=r'^qb.*'),
    Strategy(slicing=Teapot(10), name=r'^qg.*'),
    Strategy(slicing=Teapot(10), name=r'^qh.*'),
    Strategy(slicing=Teapot(10), name=r'^qi.*'),
    Strategy(slicing=Teapot(10), name=r'^qr.*'),
    Strategy(slicing=Teapot(10), name=r'^qu.*'),
    Strategy(slicing=Teapot(10), name=r'^qy.*'),
    Strategy(slicing=Teapot(50), name=r'^qa.*'),
    Strategy(slicing=Teapot(50), name=r'^qc.*'),
    # Strategy(slicing=Teapot(20), name=r'^sy\..*'), # Not taken into account for now!!!!
    # Strategy(slicing=Teapot(1), name=r'^mw\..*'),
]

line.slice_thick_elements(slicing_strategies=slicing_strategies)
line.build_tracker()
tw_thin_no_rad = line.twiss()

# Compare tunes
print('Before rematching:')

print('Tunes thick model:')
print(tw_thick_no_rad.qx, tw_thick_no_rad.qy)
print('Tunes thin model:')
print(tw_thin_no_rad.qx, tw_thin_no_rad.qy)

print('Beta beating at ips:')
print('H:', np.max(np.abs(
    tw_thin_no_rad.rows['ip.*'].betx / tw_thick_no_rad.rows['ip.*'].betx -1)))
print('V:', np.max(np.abs(
    tw_thin_no_rad.rows['ip.*'].bety / tw_thick_no_rad.rows['ip.*'].bety -1)))

print('Number of elements: ', len(line))
print('\n')

opt = line.match(
    solve=False,
    only_markers=True,
    vary=xt.VaryList(
        ['k1qf4', 'k1qf2', 'k1qd3', 'k1qd1',
         #'k1qfg2', 'k1qdg1'
         ],
        step=1e-8,
    ),
    targets=[
        xt.TargetSet(qx=tw_thick_no_rad.qx, qy=tw_thick_no_rad.qy, tol=1e-5),
    ]
)
opt.solve()
tw_thin_no_rad = line.twiss()

print('After rematching:')
print('Tunes thick model:')
print(tw_thick_no_rad.qx, tw_thick_no_rad.qy)
print('Tunes thin model:')
print(tw_thin_no_rad.qx, tw_thin_no_rad.qy)

print('Beta beating at ips:')
print('H:', np.max(np.abs(
    tw_thin_no_rad.rows['ip.*'].betx / tw_thick_no_rad.rows['ip.*'].betx -1)))
print('V:', np.max(np.abs(
    tw_thin_no_rad.rows['ip.*'].bety / tw_thick_no_rad.rows['ip.*'].bety -1)))

print('Number of elements: ', len(line))

print('Change on arc quadrupoles:')
print(opt.log().vary[-1]/opt.log().vary[0] - 1)