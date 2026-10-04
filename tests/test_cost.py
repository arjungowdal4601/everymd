"""Offline estimate arithmetic for documented Luna cache-read/write prices."""

import pytest

from everymd.api import estimate_cost


@pytest.mark.parametrize("input_tokens,output_tokens,details,expected", [
    (4122, 0, {"cache_creation": 2379, "cache_read": 1737}, 0.000315),
    (1000, 50, {"cache_creation": 400, "cache_read": 200}, 0.000117),
    (1000, 50, {"cache_read": 200}, 0.000107),
    (1000, 50, {}, 0.000125),
])
def test_luna_estimate_charges_each_input_token_once(input_tokens, output_tokens, details, expected):
    usage = {"gpt-6-luna": {"input_tokens": input_tokens, "output_tokens": output_tokens,
                            "input_token_details": details}}
    assert estimate_cost(usage) == expected


def test_cache_write_surcharge_is_applied_across_usage_entries():
    usage = {
        "gpt-6-luna": {"input_tokens": 1000, "output_tokens": 0,
                       "input_token_details": {"cache_creation": 400}},
        "gpt-6-luna-2026-09-01": {"input_tokens": 1000, "output_tokens": 0,
                                "input_token_details": {"cache_creation": 400}},
    }
    assert estimate_cost(usage) == 0.000220


def test_unknown_price_still_produces_no_estimate():
    assert estimate_cost({"unpriced-model": {"input_tokens": 1000}}) is None


def test_a_different_model_sharing_the_name_prefix_gets_no_price():
    assert estimate_cost({"gpt-6-luna-mini": {"input_tokens": 1000}}) is None
