import numpy as np

from app.engine.color import linear_to_srgb, srgb_to_linear


def test_roundtrip_is_identity():
    x = np.linspace(0, 1, 1001)
    assert np.allclose(srgb_to_linear(linear_to_srgb(x)), x, rtol=0, atol=1e-12)
    assert np.allclose(linear_to_srgb(srgb_to_linear(x)), x, rtol=0, atol=1e-12)


def test_known_values():
    assert srgb_to_linear(np.array(0.0)) == 0
    assert np.isclose(srgb_to_linear(np.array(1.0)), 1)
    # Mid-grey in a file is only about 21% of white in light.
    assert np.isclose(srgb_to_linear(np.array(0.5)), 0.2140, atol=1e-4)
