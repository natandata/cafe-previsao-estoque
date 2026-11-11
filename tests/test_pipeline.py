import unittest
import numpy as np
import pandas as pd
from src.pipeline import generate,validate_daily,forecast,backtest,Policy,levels,simulate
class ForecastTests(unittest.TestCase):
 def test_01_generator_seed(self):pd.testing.assert_frame_equal(generate(days=30),generate(days=30))
 def test_02_daily_complete(self):self.assertEqual(len(validate_daily(generate(days=30))),60)
 def test_03_missing_is_not_zero(self):
  with self.assertRaises(ValueError):validate_daily(generate(days=30).iloc[1:])
 def test_04_duplicate_rejected(self):
  x=generate(days=30)
  with self.assertRaises(ValueError):validate_daily(pd.concat([x,x.iloc[[0]]]))
 def test_05_unobserved_rejected(self):
  x=generate(days=30);x.loc[0,'observed']=False
  with self.assertRaises(ValueError):validate_daily(x)
 def test_06_negative_rejected(self):
  x=generate(days=30);x.loc[0,'quantity']=-1
  with self.assertRaises(ValueError):validate_daily(x)
 def test_07_fraction_rejected(self):
  x=generate(days=30);x['quantity']=x.quantity.astype(float);x.loc[0,'quantity']=1.2
  with self.assertRaises(ValueError):validate_daily(x)
 def test_08_closed_zero(self):
  x=generate(days=30);self.assertTrue((x.loc[~x.is_open,'quantity']==0).all())
 def test_09_closed_conflict(self):
  x=generate(days=30);i=x.index[~x.is_open][0];x.loc[i,'quantity']=1
  with self.assertRaises(ValueError):validate_daily(x)
 def test_10_unknown_recipe(self):
  x=generate(days=30);x.loc[0,'item']='Agua'
  with self.assertRaises(ValueError):validate_daily(x)
 def test_11_seasonal_exact(self):np.testing.assert_array_equal(forecast([1,2,3,4,5,6,7],10,'seasonal7'),[1,2,3,4,5,6,7,1,2,3])
 def test_12_moving_exact(self):np.testing.assert_array_equal(forecast([1,2,3,4,5,6,7],3,'moving7'),[4,4,4])
 def test_13_ses_constant(self):np.testing.assert_array_equal(forecast([8]*20,4,'ses025'),[8]*4)
 def test_14_short_history(self):
  with self.assertRaises(ValueError):forecast([1,2],1,'seasonal7')
 def test_15_bad_method(self):
  with self.assertRaises(ValueError):forecast([1]*7,1,'unknown')
 def test_16_future_invariance(self):
  y=np.arange(60,dtype=float);a=backtest(y,28,42,'moving7');y[35:]=99999;b=backtest(y,28,42,'moving7');np.testing.assert_array_equal(a.loc[a.origin==28,'prediction'],b.loc[b.origin==28,'prediction'])
 def test_17_origin_before_target(self):
  b=backtest(np.arange(60),28,56,'seasonal7');self.assertTrue((b.origin<=b['index']).all());self.assertEqual(b['index'].nunique(),28)
 def test_18_partial_horizon(self):self.assertEqual(len(backtest(np.arange(60),28,38,'moving7')),10)
 def test_19_no_cross_boundary(self):
  b=backtest(np.arange(60),28,42,'seasonal7');self.assertEqual(b['index'].max(),41)
 def test_20_invalid_window(self):
  with self.assertRaises(ValueError):backtest(np.arange(60),2,30,'seasonal7')
class InventoryTests(unittest.TestCase):
 def test_21_hand_calculated_levels(self):
  l=levels(100,0,Policy(2,.95,7,1));self.assertEqual(l,dict(rop_ml=200,target_ml=300,safety_ml=0))
 def test_22_service_raises_safety(self):self.assertGreater(levels(100,10,Policy(service=.99))['safety_ml'],levels(100,10,Policy(service=.90))['safety_ml'])
 def test_23_longer_lead_raises_rop(self):self.assertGreater(levels(100,10,Policy(lead_days=5))['rop_ml'],levels(100,10,Policy(lead_days=2))['rop_ml'])
 def test_24_invalid_policy(self):
  for kw in [dict(lead_days=0),dict(shelf_days=0),dict(service=1),dict(service=.5)]:
   with self.assertRaises(ValueError):Policy(**kw)
 def test_25_zero_demand(self):
  r,t=simulate([0]*10,0,0,Policy());self.assertEqual(r['fill_rate'],1);self.assertEqual(r['purchased_ml'],0)
 def test_26_no_negative_inventory(self):
  r,t=simulate([1000]*30,100,10,Policy());self.assertTrue((t.onhand_ml>=0).all());self.assertTrue((t.lost_ml>=0).all())
 def test_27_mass_balance(self):
  r,t=simulate([500,0,2000,0,0,0,5000,0,20],500,100,Policy())
  self.assertEqual(r['purchased_ml'],int(t.served_ml.sum())+r['waste_ml']+r['end_onhand_ml']+r['end_pipeline_ml'])
 def test_28_lost_sales_not_backlog(self):
  r,t=simulate([10000,0,0],100,0,Policy());self.assertEqual(t.served_ml.iloc[1],0);self.assertGreater(t.lost_ml.iloc[0],0)
 def test_29_no_instant_delivery(self):
  r,t=simulate([300]*5,100,0,Policy(2,.95,7,1));self.assertEqual(t.arrival_ml.iloc[0],0);self.assertEqual(t.arrival_ml.iloc[1],0);self.assertGreater(t.arrival_ml.iloc[2],0)
 def test_30_expiry_convention(self):
  r,t=simulate([0]*4,100,0,Policy(2,.95,1,1));self.assertEqual(t.expired_ml.iloc[1],300);self.assertEqual(t.onhand_ml.iloc[1],0)
 def test_31_demands_conserved(self):
  r,t=simulate([0,600,900,20]*10,300,30,Policy());self.assertTrue((t.served_ml+t.lost_ml==t.demand_ml).all())
 def test_32_seed_path_is_repeatable(self):
  a,ta=simulate([100,250,800]*7,300,30,Policy());b,tb=simulate([100,250,800]*7,300,30,Policy());self.assertEqual(a,b);pd.testing.assert_frame_equal(ta,tb)
 def test_33_invalid_ml(self):
  for d in [[-1],[.5],[float('nan')]]:
   with self.assertRaises(ValueError):simulate(d,100,10,Policy())
 def test_34_fefo_expires_old_lots(self):
  r,t=simulate([100,100,100,100,100,100],100,0,Policy(1,.95,2,1));self.assertEqual(r['waste_ml'],0)
 def test_35_empty_path(self):
  r,t=simulate([],100,0,Policy());self.assertEqual(r['fill_rate'],1);self.assertEqual(r['end_onhand_ml'],300)
 def test_36_baseline_same_demand(self):
  d=[100,200,0,1000]*4
  a,t=simulate(d,250,30,Policy(),False);b,u=simulate(d,250,30,Policy(),True);self.assertEqual(t.demand_ml.tolist(),u.demand_ml.tolist())
 def test_37_in_transit_not_double_ordered(self):
  r,t=simulate([100]*10,100,0,Policy(3,.95,8,1));self.assertTrue((t.pipeline_ml<=300).all())
 def test_38_purchase_cost_tracks_ml(self):
  r,t=simulate([100]*10,100,0,Policy());self.assertEqual(r['simulated_purchase_cents'],r['purchased_ml'])
if __name__=='__main__':unittest.main()
