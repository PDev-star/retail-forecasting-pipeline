# test_inventory.py - Unit tests for Inventory Service
"""
Test services.inventory module - pure functions, no mocking needed.
Tests calculate_stock_recommendation() business logic.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.inventory import calculate_stock_recommendation


def test_calculate_stock_recommendation():
    """Test stock recommendation calculation with standard parameters"""
    forecast = [10, 12, 11, 13, 10, 12, 11, 13, 10, 12, 11, 13, 10, 12]

    # Test with default parameters
    result = calculate_stock_recommendation(forecast, lead_time_days=14, safety_factor=1.2)

    expected_lead_time_demand = sum(forecast[:14])  # 160
    expected_recommended = int(expected_lead_time_demand * 1.2)  # 192

    assert result == expected_recommended


def test_calculate_stock_recommendation_custom_lead_time():
    """Test stock recommendation with custom lead time"""
    forecast = [10] * 30  # 30 days of 10 units/day

    result = calculate_stock_recommendation(forecast, lead_time_days=7, safety_factor=1.5)

    expected_lead_time_demand = 10 * 7  # 70
    expected_recommended = int(70 * 1.5)  # 105

    assert result == expected_recommended


def test_calculate_stock_recommendation_edge_cases():
    """Test stock recommendation with edge cases"""
    # Test with forecast shorter than lead time
    short_forecast = [10, 12, 11]
    result = calculate_stock_recommendation(short_forecast, lead_time_days=7, safety_factor=1.2)
    # Should use all available data
    expected = int(sum(short_forecast) * 1.2)
    assert result == expected

    # Test with empty forecast
    empty_forecast = []
    result = calculate_stock_recommendation(empty_forecast, lead_time_days=7, safety_factor=1.2)
    assert result == 0

    # Test with zero values
    zero_forecast = [0, 0, 0, 0, 0]
    result = calculate_stock_recommendation(zero_forecast, lead_time_days=5, safety_factor=1.2)
    assert result == 0

    # Test with single value
    single_forecast = [100]
    result = calculate_stock_recommendation(single_forecast, lead_time_days=1, safety_factor=1.5)
    assert result == 150


def test_calculate_stock_recommendation_different_safety_factors():
    """Test stock recommendation with different safety factors"""
    forecast = [50, 55, 45, 60, 50, 55, 45]

    # Test with no safety stock (factor = 1.0)
    result = calculate_stock_recommendation(forecast, lead_time_days=7, safety_factor=1.0)
    assert result == sum(forecast)

    # Test with high safety factor
    result = calculate_stock_recommendation(forecast, lead_time_days=7, safety_factor=2.0)
    assert result == sum(forecast) * 2

    # Test with low safety factor
    result = calculate_stock_recommendation(forecast, lead_time_days=7, safety_factor=0.8)
    assert result == int(sum(forecast) * 0.8)
