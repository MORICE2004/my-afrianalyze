import pytest
from pytest import approx
from packages.valuation_engine.multiples import ComparableCompany, calculate_pe_valuation, calculate_pb_valuation, calculate_ev_ebitda_valuation

def test_pe_valuation():
    """Test P/E comparable valuation."""
    peers = [
        ComparableCompany(name="A", ticker="A", exchange="DSE", pe_ratio=12.0, data_quality_note=""),
        ComparableCompany(name="B", ticker="B", exchange="DSE", pe_ratio=15.0, data_quality_note=""),
        ComparableCompany(name="C", ticker="C", exchange="DSE", pe_ratio=18.0, data_quality_note="")
    ]
    
    result = calculate_pe_valuation(100.0, peers)
    
    assert result.peer_mean == 15.0
    assert result.peer_median == 15.0
    assert result.implied_value_from_mean == 1500.0
    assert result.implied_value_from_median == 1500.0
    assert len(result.warnings) == 0

def test_pb_valuation():
    """Test P/B comparable valuation."""
    peers = [
        ComparableCompany(name="A", ticker="A", exchange="DSE", pb_ratio=1.2, data_quality_note=""),
        ComparableCompany(name="B", ticker="B", exchange="DSE", pb_ratio=1.5, data_quality_note=""),
        ComparableCompany(name="C", ticker="C", exchange="DSE", pb_ratio=1.8, data_quality_note="")
    ]
    
    result = calculate_pb_valuation(1000.0, peers)
    assert result.implied_value_from_mean == approx(1500.0)

def test_multiples_warnings():
    """Test fewer than 3 peers triggers warning."""
    peers = [
        ComparableCompany(name="A", ticker="A", exchange="DSE", pe_ratio=10.0, data_quality_note=""),
        ComparableCompany(name="B", ticker="B", exchange="DSE", pe_ratio=100.0, data_quality_note="")
    ]
    
    result = calculate_pe_valuation(10.0, peers)
    assert len(result.warnings) >= 2

def test_filtering_none_values():
    """Test filtering of missing peer data."""
    peers = [
        ComparableCompany(name="A", ticker="A", exchange="DSE", pe_ratio=10.0, data_quality_note=""),
        ComparableCompany(name="B", ticker="B", exchange="DSE", pe_ratio=None, data_quality_note="")
    ]
    
    result = calculate_pe_valuation(10.0, peers)
    assert "A" in result.peer_values
    assert "B" not in result.peer_values
