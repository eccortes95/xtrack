import numpy as np
import xtrack as xt

fname = 'fccee_t'

delta0 = 0.

num_particles_test = 300
n_turns_track_test = 400

line = xt.Line.from_json(fname + '_thin.json')
line.cycle('mwi.a4rj_entry', inplace=True)

# More voltage to stand more energy loss
line.vv['voltca1'] *= 2
line.vv['voltca2'] *= 2

# Add monitor in a dispersion-free place out of crab waist
monitor = xt.ParticlesMonitor(num_particles=num_particles_test,
                              start_at_turn=0, stop_at_turn=n_turns_track_test)
line.insert_element(element=monitor, name='monitor', index='qrdr2.3_entry')

line.build_tracker()
line.vars['on_wiggler_v'] = 0.87 / (1 + delta0)

# keep only wiggler in the first straight section
tt = line.get_table()
wigs_off = tt.rows['mwi.*', tt.element_type=='Multipole', 20000:85000:'s'].name
for nn in wigs_off:
    line.element_refs[nn].hyl = 0
    line.element_refs[nn].hxl = 0
    line.element_refs[nn].ksl[0] = 0
    line.element_refs[nn].knl[0] = 0

tw_no_rad = line.twiss(method='4d')

line.configure_radiation(model='mean')
line.compensate_radiation_energy_loss(delta0=delta0)

tw_rad = line.twiss(eneloss_and_damping=True,
                    particle_co_guess=line.build_particles(delta=delta0))

ex = tw_rad.eq_gemitt_x
ey = tw_rad.eq_gemitt_y
ez = tw_rad.eq_gemitt_zeta

line.configure_radiation(model='quantum')
p = line.build_particles(delta=delta0, num_particles=num_particles_test)
line.track(p, num_turns=n_turns_track_test, turn_by_turn_monitor=True, time=True)
mon = line.record_last_track
print(f'Tracking time: {line.time_last_track}')

import matplotlib.pyplot as plt
plt.close('all')
for ii, (mon, element_mon, label) in enumerate(
                            [(line.record_last_track, 0, 'inside crab waste'),
                             (monitor, 'monitor', 'outside crab waste')]):

    betx = tw_rad['betx', element_mon]
    bety = tw_rad['bety', element_mon]
    betx2 = tw_rad['betx2', element_mon]
    bety1 = tw_rad['bety1', element_mon]
    dx = tw_rad['dx', element_mon]
    dy = tw_rad['dy', element_mon]

    fig = plt.figure(ii + 1, figsize=(6.4, 4.8*1.3))
    spx = fig. add_subplot(3, 1, 1)
    spx.plot(np.std(mon.x, axis=0), label='track')
    spx.axhline(
        np.sqrt(ex * betx + ey * betx2 + (np.std(p.delta) * dx)**2),
        color='red', label='twiss')
    spx.legend(loc='lower right')
    spx.set_ylabel(r'$\sigma_{x}$ [m]')
    spx.set_ylim(bottom=0)

    spy = fig. add_subplot(3, 1, 2, sharex=spx)
    spy.plot(np.std(mon.y, axis=0), label='track')
    spy.axhline(
        np.sqrt(ex * bety1 + ey * bety + (np.std(p.delta) * dy)**2),
        color='red', label='twiss')
    spy.set_ylabel(r'$\sigma_{y}$ [m]')
    spy.set_ylim(bottom=0)

    spz = fig. add_subplot(3, 1, 3, sharex=spx)
    spz.plot(np.std(mon.zeta, axis=0))
    spz.axhline(np.sqrt(ez * tw_rad.betz0), color='red')
    spz.set_ylabel(r'$\sigma_{z}$ [m]')
    spz.set_ylim(bottom=0)

    plt.suptitle(f'{fname} - ' r'$\varepsilon_y$ = ' f'{ey*1e12:.6f} pm - {label}')

plt.show()
