# Loop 032 log (1 linia / iteracja)

it1: merge_gap_mult 2.5->3.0 (line_tracer.py:314) | COFNIETE p033 -1.81

it2: hough_bus_gap_frac 0.004->0.0045 (runtime.yaml:57) | sr 19.49->19.65 | p028 +0.07 p029 +0.43 p030 -0.21 p031 0 p033 +0.66 p034 0 OK

it3: contact/join_frac 0.013, min_len_frac 0.019 | COFNIETE brak delty p033/p028

it4: L2 snap+probe_tol+T-odczep (line_sieve) | COFNIETE sr 19.65->17.60 | diag: za agresywne sito, p028/p029 regresja

it4: L2 L-corner net_builder | COFNIETE sr 19.65->19.50 p033 -0.66 | falszywe scalenia netow

it4: probe yolo_conf 0.15 | COFNIETE brak delty | next L3 conn topology / p031 MODEL
it5: diag p034 zlaczka GT x=5558 vs RT x=442 IoU=0 | p028 conn 1/42 match | brak bezpiecznej zmiany

