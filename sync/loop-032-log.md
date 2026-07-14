# Loop 032 log (1 linia / iteracja)



it1: merge_gap_mult 2.5->3.0 (line_tracer.py:314) | COFNIETE p033 -1.81



it2: hough_bus_gap_frac 0.004->0.0045 (runtime.yaml:57) | sr 19.49->19.65 | p028 +0.07 p029 +0.43 p030 -0.21 p031 0 p033 +0.66 p034 0 OK



it3: contact/join_frac 0.013, min_len_frac 0.019 | COFNIETE brak delty p033/p028



it4: L2 snap+probe_tol+T-odczep (line_sieve) | COFNIETE sr 19.65->17.60 | diag: za agresywne sito, p028/p029 regresja



it4: L2 L-corner net_builder | COFNIETE sr 19.65->19.50 p033 -0.66 | falszywe scalenia netow



it4: probe yolo_conf 0.15 | COFNIETE brak delty | next L3 conn topology / p031 MODEL

it5: diag p034 zlaczka GT x=5558 vs RT x=442 IoU=0 | p028 conn 1/42 match | brak bezpiecznej zmiany

it6: L2 refine_arrow_bboxes landscape-only (arrow_supplement.py) | sr 19.65->20.86 | p030 +9.21 p028 -0.07 p029 -0.42 p033 -0.62 p034 -0.89 OK

it7: L2 portrait refine + discover coarse 0.40 | COFNIETE sr 20.86->20.65 p029 -2.01 | discover FP / portrait psuje p029

it8: L2 discover gdy YOLO=0 strzalek | COFNIETE sr 20.86->19.93 p030 -4.28 p028 -1.26 | discover + scales bug

it9: L2 _template_scale przy downscale coarse (arrow_supplement.py) | sr 20.86->20.96 | p028 +1.33 p029 +0.02 p030 -0.71 OK | diag: szablon full-res na obrazie 0.5x -> 0 trafien

it10: L2 coarse peak NMS zamiast np.where (arrow_supplement.py) | sr 20.96->21.05 | p028 +0.50 p029 0 OK | diag: wyjsciowa 16 FP RT / 9 GT

it11: L2 portrait refine supplement class_id=-1 (arrow_supplement.py) | sr 21.05->21.24 | p028 +1.16 p029 0 OK | diag: wyjsciowa bbox 40x72 bez refine, GT 61-85px

STOP: plateau it9/it10/it11 (Δ<1.0×3) | sr 19.49->21.24 | 5 decyzji | pytest 281 | val 30.77

