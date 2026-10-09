"""LiGaMD thermodynamic reweighting and *biased-trajectory* event statistics.

Input CSV: step,distance_A,boost_kcal_mol. Boost is the SUM of boosts.
Step is the MD integration step, not a CPPTRAJ frame index.
"""
from __future__ import annotations
import argparse
import numpy as np

KB = 0.00198720425864083  # kcal mol^-1 K^-1


def _vector(values, name):
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or not len(values) or not np.all(np.isfinite(values)):
        raise ValueError(f'{name} must be a nonempty finite 1D array')
    return values


def reweighted_mean(observable, boost, beta):
    """Normalized exponential estimator; numerical stability is not convergence."""
    observable = _vector(observable, 'observable')
    boost = _vector(boost, 'boost')
    if observable.shape != boost.shape or not np.isfinite(beta) or beta <= 0:
        raise ValueError('aligned arrays and a positive finite beta are required')
    logw = beta * boost
    weights = np.exp(logw - logw.max())
    return float(np.dot(observable, weights) / weights.sum())


def calculate_pmf_ligamd(coordinate, boost, beta, bins=50, min_count=10):
    """Second-order binwise cumulant PMF. Returns centers, PMF, counts.

    F_i = -ln(n_i / bin_width_i)/beta - mean(boost)_i
          - beta*var(boost)_i/2 + constant.
    Assumes fixed production bias and near-Gaussian conditional boost distributions.
    This is a coordinate-density PMF, without radial Jacobian/standard-state correction.
    """
    coordinate = _vector(coordinate, 'coordinate')
    boost = _vector(boost, 'boost')
    if coordinate.shape != boost.shape or not np.isfinite(beta) or beta <= 0:
        raise ValueError('aligned arrays and positive finite beta are required')
    if not isinstance(min_count, (int, np.integer)) or min_count < 1:
        raise ValueError('min_count must be a positive integer')
    counts, edges = np.histogram(coordinate, bins=bins)
    if np.any(np.diff(edges) <= 0):
        raise ValueError('bin edges must increase')
    bin_ids = np.searchsorted(edges, coordinate, side='right') - 1
    bin_ids[coordinate == edges[-1]] = len(counts) - 1
    pmf = np.full(len(counts), np.nan)
    for i, count in enumerate(counts):
        if count < min_count:
            continue
        local_boost = boost[bin_ids == i]
        pmf[i] = (-np.log(count / (edges[i+1]-edges[i])) / beta
                  - local_boost.mean() - 0.5 * beta * local_boost.var())
    if not np.any(np.isfinite(pmf)):
        raise ValueError('no sufficiently populated bins; collect more samples')
    pmf -= np.nanmin(pmf)
    return 0.5 * (edges[:-1] + edges[1:]), pmf, counts


def detect_events(distance, d_bound=5.0, d_unbound=10.0, min_confirm_frames=1):
    """Hysteretic states: retain the last core state through the intermediate region.

    0=not yet assigned, 1=bound, 2=unbound. A transition needs consecutive
    observations in the opposite core; once confirmed it starts at that run's
    first frame. Choose confirmation time using output cadence and sensitivity tests.
    Event durations include intermediate transit and can be left-censored.
    """
    distance = _vector(distance, 'distance')
    if not 0 <= d_bound < d_unbound or min_confirm_frames < 1:
        raise ValueError('ordered nonnegative thresholds and confirmation >=1 required')
    if int(min_confirm_frames) != min_confirm_frames:
        raise ValueError('min_confirm_frames must be an integer')
    states = np.zeros(len(distance), dtype=int)
    events = []
    current = 0
    candidate = 0
    run_start = 0
    state_start = 0
    for i, value in enumerate(distance):
        core = 1 if value < d_bound else 2 if value > d_unbound else 0
        states[i] = current
        if core == 0 or core == current:
            candidate = 0
            continue
        if core != candidate:
            candidate, run_start = core, i
        if i - run_start + 1 >= min_confirm_frames:
            if current:
                events.append({'type': f'{current}->{core}',
                               'start_frame': state_start, 'end_frame': run_start,
                               'duration_frames': run_start - state_start})
            current, state_start = core, run_start
            states[run_start:i+1] = current
            candidate = 0
    return states, events


def estimate_biased_kinetics(states, frame_dt_ns, ligand_concentration_M=None):
    """Apparent event/exposure estimates ONLY; not true LiGaMD kinetic rates.

    Assumes a two-state process and uniform frame intervals. Terminal intervals
    contribute exposure (right-censoring). No Kd is inferred from biased rates.
    Concentration must match the chosen single-ligand/site-event convention.
    """
    states = np.asarray(states)
    if states.ndim != 1 or len(states) < 2 or not np.all(np.isin(states, [0,1,2])):
        raise ValueError('at least two states in {0,1,2} required')
    if not np.isfinite(frame_dt_ns) or frame_dt_ns <= 0:
        raise ValueError('positive finite frame_dt_ns required')
    if ligand_concentration_M is not None:
        if not np.isfinite(ligand_concentration_M) or ligand_concentration_M <= 0:
            raise ValueError('positive finite concentration required')
    previous, following = states[:-1], states[1:]
    n_unbinding = int(np.sum((previous == 1) & (following == 2)))
    n_binding = int(np.sum((previous == 2) & (following == 1)))
    bound_s = np.sum(previous == 1) * frame_dt_ns * 1e-9
    unbound_s = np.sum(previous == 2) * frame_dt_ns * 1e-9
    koff = n_unbinding / bound_s if bound_s else np.nan
    association_s = n_binding / unbound_s if unbound_s else np.nan
    kon = association_s / ligand_concentration_M if ligand_concentration_M is not None else np.nan
    return dict(n_unbinding=n_unbinding, n_binding=n_binding,
                bound_exposure_s=float(bound_s), unbound_exposure_s=float(unbound_s),
                k_off_biased_s_inv=float(koff),
                association_biased_s_inv=float(association_s),
                k_on_biased_M_inv_s_inv=float(kon))


def pmf_level_difference(xi, pmf, bound_range=(0,5), unbound_range=(10,20)):
    """Unbound-minus-bound profile level difference; NOT standard binding free energy."""
    xi, pmf = np.asarray(xi), np.asarray(pmf)
    if xi.shape != pmf.shape or xi.ndim != 1:
        raise ValueError('aligned 1D arrays required')
    bound = (xi >= bound_range[0]) & (xi <= bound_range[1]) & np.isfinite(pmf)
    unbound = (xi >= unbound_range[0]) & (xi <= unbound_range[1]) & np.isfinite(pmf)
    if not bound.any() or not unbound.any():
        raise ValueError('both ranges need finite sampled bins')
    return float(pmf[unbound].mean() - pmf[bound].min())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', help='aligned production-only CSV with named columns')
    parser.add_argument('--dt-ps', type=float, required=True, help='MD integration step in ps')
    parser.add_argument('--temperature', type=float, default=300)
    parser.add_argument('--bins', type=int, default=50)
    parser.add_argument('--min-count', type=int, default=10)
    parser.add_argument('--d-bound', type=float, default=5)
    parser.add_argument('--d-unbound', type=float, default=10)
    parser.add_argument('--confirm-frames', type=int, default=1)
    parser.add_argument('--concentration-M', type=float)
    parser.add_argument('--output', default='ligamd_pmf.csv')
    args = parser.parse_args()
    if not np.isfinite(args.temperature) or args.temperature <= 0:
        parser.error('temperature must be positive and finite')
    if not np.isfinite(args.dt_ps) or args.dt_ps <= 0:
        parser.error('dt-ps must be positive and finite')
    data = np.atleast_1d(np.genfromtxt(args.csv, delimiter=',', names=True))
    required = {'step','distance_A','boost_kcal_mol'}
    if data.dtype.names is None or not required.issubset(data.dtype.names):
        parser.error('CSV needs step,distance_A,boost_kcal_mol columns')
    steps = _vector(data['step'], 'step')
    if len(steps) < 2 or np.any(steps != np.floor(steps)):
        parser.error('at least two integer MD steps required')
    intervals = np.diff(steps)
    if np.any(intervals <= 0) or not np.all(intervals == intervals[0]):
        parser.error('MD steps must strictly increase at uniform intervals')
    frame_dt_ns = intervals[0] * args.dt_ps / 1000
    distance = data['distance_A']
    beta = 1 / (KB * args.temperature)
    xi, pmf, counts = calculate_pmf_ligamd(distance, data['boost_kcal_mol'], beta,
                                         args.bins, args.min_count)
    np.savetxt(args.output, np.column_stack([xi,pmf,counts]), delimiter=',',
               header='distance_A,pmf_kcal_mol,count', comments='')
    states, events = detect_events(distance, args.d_bound, args.d_unbound, args.confirm_frames)
    kinetics = estimate_biased_kinetics(states, frame_dt_ns, args.concentration_M)
    print(f'Frame spacing: {frame_dt_ns:g} ns; confirmed events: {len(events)}')
    print('Biased-trajectory statistics only; no physical kinetic correction or Kd:')
    for name, value in kinetics.items():
        print(f'{name}: {value}')
    print('PMF is a binwise second-order approximation; check sampling, Gaussianity,')
    print('block/replicate convergence, radial geometry and standard-state corrections.')


if __name__ == '__main__':
    main()
