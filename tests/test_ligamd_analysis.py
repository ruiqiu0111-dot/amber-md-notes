import unittest
import numpy as np
from analysis.ligamd_analysis import (KB, calculate_pmf_ligamd, reweighted_mean,
                                      detect_events, estimate_biased_kinetics)

class ReweightingTests(unittest.TestCase):
    def setUp(self):
        self.beta = 1 / (KB * 300)

    def test_constant_boost_recovers_population_pmf_and_right_edge(self):
        x = np.r_[np.zeros(90), np.full(10,1.5)]
        _, pmf, counts = calculate_pmf_ligamd(x, np.full(100,7.), self.beta,
                                             bins=[-.5,.5,1.5], min_count=1)
        np.testing.assert_array_equal(counts, [90,10])
        self.assertAlmostEqual(pmf[1]-pmf[0], np.log(9)/self.beta)

    def test_conditional_boost_mean_is_retained(self):
        x = np.repeat([0.,1.], 20)
        v = np.repeat([1.,3.], 20)
        _, pmf, _ = calculate_pmf_ligamd(x,v,self.beta,bins=[-.5,.5,1.5])
        self.assertAlmostEqual(pmf[1]-pmf[0], -2.)

    def test_normalization_and_large_boost_stability(self):
        self.assertAlmostEqual(reweighted_mean(np.ones(2), [10000,10002], self.beta), 1.)
        expected = 2*np.exp(2*self.beta)/(1+np.exp(2*self.beta))
        self.assertAlmostEqual(reweighted_mean([0,2],[10000,10002],self.beta), expected)

    def test_boost_shift_invariance(self):
        x = np.repeat([0.,1.], 20)
        v = np.arange(40)/20
        result1 = calculate_pmf_ligamd(x,v,self.beta,bins=2)[1]
        result2 = calculate_pmf_ligamd(x,v+100,self.beta,bins=2)[1]
        np.testing.assert_allclose(result1,result2,atol=1e-12)

    def test_bin_width_and_empty_bins(self):
        x = np.r_[np.full(20,.5),np.full(40,2.)]
        _, pmf, _ = calculate_pmf_ligamd(x,np.zeros(60),self.beta,bins=[0,1,3,4])
        self.assertAlmostEqual(pmf[0],pmf[1])
        self.assertTrue(np.isnan(pmf[2]))

    def test_invalid_or_misaligned_data_fail(self):
        with self.assertRaises(ValueError):
            calculate_pmf_ligamd([0,1],[0],self.beta)
        with self.assertRaises(ValueError):
            reweighted_mean([1,np.nan],[0,1],self.beta)
        with self.assertRaises(ValueError):
            calculate_pmf_ligamd([0,1],[0,1],self.beta,min_count=10)

class EventTests(unittest.TestCase):
    def test_intermediate_state_does_not_reverse_event(self):
        states,events=detect_events([4,7,11])
        np.testing.assert_array_equal(states,[1,1,2])
        self.assertEqual([e['type'] for e in events],['1->2'])
        stats=estimate_biased_kinetics(states,frame_dt_ns=.02)
        self.assertEqual(stats['n_unbinding'],1)
        self.assertEqual(stats['n_binding'],0)
        np.testing.assert_allclose(stats['k_off_biased_s_inv'], 1/(.04e-9), rtol=1e-12)

    def test_confirmation_filters_short_excursion(self):
        states,events=detect_events([4,4,11,7,11,11],min_confirm_frames=2)
        np.testing.assert_array_equal(states,[1,1,1,1,2,2])
        self.assertEqual(len(events),1)
        self.assertEqual(events[0]['end_frame'],4)

    def test_initial_unknown_not_counted_and_concentration_units(self):
        states,events=detect_events([7,11,7,4])
        np.testing.assert_array_equal(states,[0,2,2,1])
        self.assertEqual([e['type'] for e in events],['2->1'])
        stats=estimate_biased_kinetics(states,1,ligand_concentration_M=.001)
        self.assertAlmostEqual(stats['k_on_biased_M_inv_s_inv'],1/(2e-9*.001))
        self.assertNotIn('K_d',stats)

    def test_terminal_exposure_counts_without_terminal_event(self):
        stats=estimate_biased_kinetics([1,1,1],1)
        self.assertEqual(stats['n_unbinding'],0)
        self.assertAlmostEqual(stats['bound_exposure_s'],2e-9)
        self.assertTrue(np.isnan(stats['association_biased_s_inv']))

if __name__ == '__main__':
    unittest.main()
