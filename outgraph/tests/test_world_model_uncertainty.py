"""Test Suite for Stage 4.4: Uncertainty Propagation Engine."""

import pytest

from outgraph.ml.world_model.uncertainty import (
    UncertaintyType,
    PhysicalUncertainty,
    UncertaintyChain,
    UncertaintyPropagator,
)


def test_uncertainty_preservation_types():
    # 1. Scalar
    u_scalar = PhysicalUncertainty.scalar(0.25, unit="meters", source="OHRC_GSD")
    assert u_scalar.uncertainty_type == UncertaintyType.SCALAR
    assert u_scalar.scalar_value == 0.25

    # 2. Interval
    u_interval = PhysicalUncertainty.interval(0.25, 59.2, unit="meters", source="GSD_TO_DEM_SPAN")
    assert u_interval.uncertainty_type == UncertaintyType.INTERVAL
    assert u_interval.interval_bounds == [0.25, 59.2]

    # 3. Covariance
    cov = [[0.05, 0.01], [0.01, 0.04]]
    u_cov = PhysicalUncertainty.covariance(cov, unit="meters_sq", source="GROUNDGRID_RESIDUAL")
    assert u_cov.uncertainty_type == UncertaintyType.COVARIANCE
    assert u_cov.covariance_matrix == cov

    # 4. Qualitative
    u_qual = PhysicalUncertainty.qualitative("HIGH_EPISTEMIC_RISK", source="ILLUMINATION_SHADOW")
    assert u_qual.uncertainty_type == UncertaintyType.QUALITATIVE
    assert u_qual.qualitative_label == "HIGH_EPISTEMIC_RISK"

    # 5. Unknown
    u_unk = PhysicalUncertainty.unknown(source="NO_MEASUREMENT")
    assert u_unk.uncertainty_type == UncertaintyType.UNKNOWN
    assert u_unk.scalar_value is None


def test_geometric_uncertainty_propagation():
    # OHRC GSD = 0.25m, SLDEM2015 res = 59.2m, Parallax corridor width = 20.3m
    geom_unc = UncertaintyPropagator.propagate_geometric_uncertainty(
        source_res_m=0.25,
        dem_res_m=59.2,
        corridor_width_m=20.3,
        sensor_type="OHRC",
    )
    assert geom_unc.uncertainty_type == UncertaintyType.INTERVAL
    assert geom_unc.interval_bounds is not None
    # Lower bound is sensor GSD
    assert geom_unc.interval_bounds[0] == 0.25
    # Upper bound is sqrt(0.25^2 + 59.2^2 + 20.3^2) ~ 62.58
    assert 60.0 < geom_unc.interval_bounds[1] < 65.0


def test_association_uncertainty_propagation():
    geom_unc = PhysicalUncertainty.interval(0.25, 62.58, unit="meters", source="GEOMETRY")

    # Inside spatial tolerance (distance = 35.0 m, tolerance = 200.0 m)
    assoc_unc = UncertaintyPropagator.propagate_association_uncertainty(
        geom_uncertainty=geom_unc,
        spatial_distance_m=35.0,
        spatial_tolerance_m=200.0,
    )
    assert assoc_unc.uncertainty_type == UncertaintyType.INTERVAL
    assert assoc_unc.interval_bounds == [0.25, round(62.58 + 35.0, 2)]

    # Outside spatial tolerance (distance = 1500.0 m > 200.0 m)
    assoc_out = UncertaintyPropagator.propagate_association_uncertainty(
        geom_uncertainty=geom_unc,
        spatial_distance_m=1500.0,
        spatial_tolerance_m=200.0,
    )
    assert assoc_out.uncertainty_type == UncertaintyType.QUALITATIVE
    assert assoc_out.qualitative_label == "REJECTED_OUT_OF_BOUNDS"


def test_no_silent_confidence_on_unknown():
    unk_geom = PhysicalUncertainty.unknown()
    assoc_unc = UncertaintyPropagator.propagate_association_uncertainty(
        geom_uncertainty=unk_geom,
        spatial_distance_m=10.0,
        spatial_tolerance_m=200.0,
    )
    # Must remain explicitly UNKNOWN
    assert assoc_unc.uncertainty_type == UncertaintyType.UNKNOWN
    assert assoc_unc.scalar_value is None


def test_traceable_uncertainty_chain():
    src_u = PhysicalUncertainty.scalar(0.25, unit="meters", source="OHRC_DETECTOR")
    geom_u = PhysicalUncertainty.interval(0.25, 62.58, unit="meters", source="SLDEM2015_PARALLAX")
    assoc_u = PhysicalUncertainty.interval(0.25, 97.58, unit="meters", source="SPATIAL_OFFSET")

    chain = UncertaintyPropagator.build_chain(
        source_unc=src_u,
        geom_unc=geom_u,
        assoc_unc=assoc_u,
    )
    assert chain.source_uncertainty.source == "OHRC_DETECTOR"
    assert chain.geometry_uncertainty.source == "SLDEM2015_PARALLAX"
    assert chain.association_uncertainty.source == "SPATIAL_OFFSET"
    assert chain.correspondence_uncertainty is None
