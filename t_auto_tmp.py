from backend.recognize.line_tracer import auto_line_params, LineTracer
def test_auto():
    ml,h,g = auto_line_params(6617,4678)
    assert (ml,h,g)==(round(0.02*6617), round(0.02*6617), round(0.0015*6617)), (ml,h,g)
    assert auto_line_params(120,120)==(20,50,4)
def test_override():
    assert LineTracer(min_line_length=20)._params(6617,4678)[0]==20
    # default auto on big page
    assert LineTracer()._params(6617,4678)==(132,132,10)
