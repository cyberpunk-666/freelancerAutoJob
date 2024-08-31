import pytest
import os
import sys

# Get the root directory (parent directory of the test directory)
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add the root directory to sys.path
sys.path.insert(0, root_dir)
from job_application_processor import JobApplicationProcessor

@pytest.fixture
def processor():
    return JobApplicationProcessor()

def test_is_budget_acceptable_hourly_rate_below_minimum(processor, monkeypatch):
    monkeypatch.setenv('MIN_HOURLY_RATE', '50')
    assumption_and_time = {"estimated_time": "10 hours"}
    budget_info = {"min_budget_cad": 40, "max_budget_cad": 500, "rate_type": "hourly"}
    assert processor.is_budget_acceptable(assumption_and_time, budget_info) == True

def test_is_budget_acceptable_total_cost_within_budget(processor, monkeypatch):
    monkeypatch.setenv('MIN_HOURLY_RATE', '50')
    assumption_and_time = {"estimated_time": "5 hours"}
    budget_info = {"min_budget_cad": 200, "max_budget_cad": 300, "rate_type": "fixed"}
    assert processor.is_budget_acceptable(assumption_and_time, budget_info) == True

def test_is_budget_acceptable_total_cost_exceeds_budget(processor, monkeypatch):
    monkeypatch.setenv('MIN_HOURLY_RATE', '50')
    assumption_and_time = {"estimated_time": "10 hours"}
    budget_info = {"min_budget_cad": 200, "max_budget_cad": 400, "rate_type": "fixed"}
    assert processor.is_budget_acceptable(assumption_and_time, budget_info) == False

def test_is_budget_acceptable_no_estimated_time(processor, monkeypatch):
    monkeypatch.setenv('MIN_HOURLY_RATE', '50')
    assumption_and_time = {"estimated_time": ""}
    budget_info = {"min_budget_cad": 200, "max_budget_cad": 1000, "rate_type": "fixed"}
    assert processor.is_budget_acceptable(assumption_and_time, budget_info) == True

def test_is_budget_acceptable_invalid_max_budget(processor, monkeypatch):
    monkeypatch.setenv('MIN_HOURLY_RATE', '50')
    assumption_and_time = {"estimated_time": "5 hours"}
    budget_info = {"min_budget_cad": 200, "max_budget_cad": "invalid", "rate_type": "fixed"}
    assert processor.is_budget_acceptable(assumption_and_time, budget_info) == False

def test_is_budget_acceptable_no_min_hourly_rate(processor, monkeypatch):
    monkeypatch.delenv('MIN_HOURLY_RATE', raising=False)
    assumption_and_time = {"estimated_time": "5 hours"}
    budget_info = {"min_budget_cad": 200, "max_budget_cad": 1000, "rate_type": "fixed"}
    assert processor.is_budget_acceptable(assumption_and_time, budget_info) == True
