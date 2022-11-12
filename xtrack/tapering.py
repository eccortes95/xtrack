import numpy as np
from scipy.constants import c as clight

def compensate_radiation_energy_loss(tracker, rtot_eneloss=1e-10, max_iter=100, **kwargs):

    line = tracker.line

    print("Compensating energy loss:")

    print("  - Twiss with no radiation")
    tracker.configure_radiation(mode=None)
    tw_no_rad = tracker.twiss(method='4d', freeze_longitudinal=True, **kwargs)

    print("  - Identify multipoles and cavities")
    line_df = line.to_pandas()
    multipoles = line_df[line_df['element_type'] == 'Multipole']
    cavities = line_df[line_df['element_type'] == 'Cavity'].copy()

    # save voltages
    cavities['voltage'] = [cc.voltage for cc in cavities.element.values]
    cavities['frequency'] = [cc.frequency for cc in cavities.element.values]
    cavities['eneloss_partitioning'] = cavities['voltage'] / cavities['voltage'].sum()

    # Put all cavities on crest and at zero frequency
    print("  - Put all cavities on crest and set zero voltage and frequency")
    for cc in cavities.element.values:
        cc.lag = 90.
        cc.voltage = 0.
        cc.frequency = 0.

    print("Share energy loss among cavities (repeat until energy loss is zero)")
    tracker.configure_radiation(mode='mean')
    tracker.config.XTRACK_MULTIPOLE_TAPER = True
    try:
        i_iter = 0
        while True:
            p_test = tw_no_rad.particle_on_co.copy()
            tracker.configure_radiation(mode='mean')
            tracker.track(p_test, turn_by_turn_monitor='ONE_TURN_EBE')
            mon = tracker.record_last_track

            eloss = -(mon.ptau[0, -1] - mon.ptau[0, 0]) * p_test.p0c[0]
            print(f"Energy loss: {eloss:.3f} eV             ", end='\r', flush=True)

            if eloss < p_test.energy0[0]*rtot_eneloss:
                break

            for ii in cavities.index:
                cc = cavities.loc[ii, 'element']
                eneloss_partitioning = cavities.loc[ii, 'eneloss_partitioning']
                cc.voltage += eloss * eneloss_partitioning

            i_iter += 1
            if i_iter > max_iter:
                raise RuntimeError("Maximum number of iterations reached")

    except Exception as e:
        tracker.config.XTRACK_MULTIPOLE_TAPER = False
        raise e

    print()

    tracker.config.XTRACK_MULTIPOLE_TAPER = False

    print("  - Adjust multipole strengths")
    i_multipoles = multipoles.index.values
    delta_taper = ((mon.delta[0,:][i_multipoles+1] + mon.delta[0,:][i_multipoles]) / 2)
    for nn, dd in zip(multipoles['name'].values, delta_taper):
        line[nn].knl *= (1 + dd)
        line[nn].ksl *= (1 + dd)

    print("  - Restore cavity voltage and frequency. Set cavity lag")
    beta0 = p_test.beta0[0]
    v_ratio = []
    for icav in cavities.index:
        v_ratio.append(cavities.loc[icav, 'element'].voltage / cavities.loc[icav, 'voltage'])
        inst_phase = np.arcsin(cavities.loc[icav, 'element'].voltage / cavities.loc[icav, 'voltage'])
        freq = cavities.loc[icav, 'frequency']

        zeta = mon.zeta[0, icav]
        lag = 360.*(inst_phase / (2*np.pi) - freq*zeta/beta0/clight)
        lag = 180. - lag # we are above transition

        cavities.loc[icav, 'element'].lag = lag
        cavities.loc[icav, 'element'].frequency = freq
        cavities.loc[icav, 'element'].voltage = cavities.loc[icav, 'voltage']