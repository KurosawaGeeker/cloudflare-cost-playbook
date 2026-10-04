#!/usr/bin/env python3
"""Estimate marginal Workers/R2 usage; never queries or mutates Cloudflare."""
import argparse
import json
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP
from pathlib import Path

MILLION = Decimal(1_000_000)
PRICING = Path(__file__).resolve().parents[1] / "references" / "pricing.json"


def number(value, field, integer=False):
    if isinstance(value, bool):
        raise ValueError(f"{field} must be numeric, not boolean")
    try:
        result = Decimal(str(value))
    except Exception as error:
        raise ValueError(f"{field} must be numeric") from error
    if not result.is_finite() or result < 0 or (integer and result != result.to_integral_value()):
        raise ValueError(f"{field} must be a finite nonnegative {'integer' if integer else 'number'}")
    return result


def money(value):
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def estimate(data, prices=None):
    prices = prices or json.loads(PRICING.read_text())
    counts = {key: number(data[key], key, integer=True) for key in (
        "public_reads", "vote_posts", "publisher_invocations", "worker_cpu_ms_before", "worker_cpu_ms_after",
        "r2_class_a_operations", "r2_class_b_other_operations")}
    read_path = data["read_path"]
    if read_path not in ("direct_r2", "worker_proxy"):
        raise ValueError("read_path must be direct_r2 or worker_proxy")
    days = number(data["window_days"], "window_days")
    if days == 0 or days > 31:
        raise ValueError("window_days must be >0 and <=31")
    fraction = number(data["origin_fraction"], "origin_fraction")
    if fraction > 1:
        raise ValueError("origin_fraction must be <=1")
    operations_per_origin = number(data["r2_operations_per_origin_read"], "r2_operations_per_origin_read")
    quota = data["monthly_allowance"]
    allowances = {key: number(quota[key], key, integer=True) for key in (
        "worker_requests", "worker_cpu_ms", "r2_class_a", "r2_class_b")}
    allowances["r2_storage_gb_month"] = number(quota["r2_storage_gb_month"], "r2_storage_gb_month allowance")
    prior = data["account_usage_before_window"]
    prior_usage = {key: number(prior[key], f"prior {key}", integer=True) for key in (
        "worker_requests", "worker_cpu_ms", "r2_class_a", "r2_class_b")}
    prior_usage["r2_storage_gb_month"] = number(prior["r2_storage_gb_month"], "prior r2_storage_gb_month")
    storage = number(data["r2_storage_gb_month"], "r2_storage_gb_month")
    rate = {key: number(prices[key], key) for key in (
        "workers_requests_per_million", "workers_cpu_ms_per_million", "r2_class_a_per_million",
        "r2_class_b_per_million", "r2_storage_per_gb_month")}

    def linear(used, key, price):
        def charge(quantity):
            return max(Decimal(0), quantity - allowances[key]) / MILLION * price
        return charge(prior_usage[key] + used) - charge(prior_usage[key])

    def rounded(used, key, unit, price):
        def charge(quantity):
            return (max(Decimal(0), quantity - allowances[key]) / unit).to_integral_value(rounding=ROUND_CEILING) * price
        return charge(prior_usage[key] + used) - charge(prior_usage[key])

    origin_reads = (counts["public_reads"] * fraction * operations_per_origin).to_integral_value(rounding=ROUND_CEILING) + counts["r2_class_b_other_operations"]
    puts = counts["r2_class_a_operations"]
    before_calls = counts["public_reads"] + counts["vote_posts"]
    after_calls = counts["vote_posts"] + counts["publisher_invocations"] + (counts["public_reads"] if read_path == "worker_proxy" else 0)
    before_req = linear(before_calls, "worker_requests", rate["workers_requests_per_million"])
    after_req = linear(after_calls, "worker_requests", rate["workers_requests_per_million"])
    before_cpu = linear(counts["worker_cpu_ms_before"], "worker_cpu_ms", rate["workers_cpu_ms_per_million"])
    after_cpu = linear(counts["worker_cpu_ms_after"], "worker_cpu_ms", rate["workers_cpu_ms_per_million"])
    reads = rounded(origin_reads, "r2_class_b", MILLION, rate["r2_class_b_per_million"])
    writes = rounded(puts, "r2_class_a", MILLION, rate["r2_class_a_per_million"])
    storage_fee = rounded(storage, "r2_storage_gb_month", Decimal(1), rate["r2_storage_per_gb_month"])
    freshness = data.get("freshness")
    freshness_result = {"checked": False, "note": "No freshness inputs; a low price does not prove acceptable data delay."}
    if freshness is not None:
        components = {key: number(freshness[key], key) for key in (
            "publication_seconds", "cdn_ttl_seconds", "browser_ttl_seconds", "poll_seconds", "target_seconds")}
        delay = sum(components[key] for key in components if key != "target_seconds")
        freshness_result = {"checked": True, "healthy_delay_budget_seconds": str(delay),
                            "target_seconds": str(components["target_seconds"]),
                            "within_target_assuming_healthy_services": delay <= components["target_seconds"],
                            "note": "Simple conservative sum; excludes network, scheduler jitter, retries and failures. Not a guaranteed bound."}
    return {
        "label": data.get("label", "explicit-input scenario"),
        "currency": prices["currency"], "pricing_verified_on": prices["verified_on"],
        "window_days": str(days), "read_path": read_path, "true_origin_fraction": str(fraction),
        "quantities": {"worker_requests_before": int(before_calls), "worker_requests_after": int(after_calls),
                       "r2_class_b_reads": int(origin_reads), "r2_class_a_operations": int(puts)},
        "freshness": freshness_result,
        "before": {"worker_request_usd": money(before_req), "worker_cpu_usd": money(before_cpu),
                   "modeled_usage_usd": money(before_req + before_cpu)},
        "after": {"worker_request_usd": money(after_req), "worker_cpu_usd": money(after_cpu),
                  "r2_read_usd": money(reads), "r2_write_usd": money(writes),
                  "r2_storage_usd": money(storage_fee), "modeled_usage_usd": money(after_req + after_cpu + reads + writes + storage_fee)},
        "assumptions": [
            "Mutually exclusive architectures for the same traffic, not two estimates to add together.",
            "Inputs represent one window <=31 days within one billing cycle; allowances and prior usage belong to that same account and cycle.",
            "Marginal cost is charge(prior account usage + scenario) minus charge(prior account usage), including R2 rounding across shared workloads.",
            ("Public reads access a cache-enabled R2 custom domain directly, with no user Worker on that path." if read_path == "direct_r2" else "All public reads enter a Worker proxy before its cache/R2 access; all are counted as Worker requests."),
            "Origin fraction is the fraction of public reads reaching R2 after all cache tiers; operation amplification and other Class B operations are explicit inputs.",
            "Publisher Worker invocations and R2 Class A operations are measured or modeled independently; DO alarms/external publishers have other excluded costs.",
            "R2 operations and GB-month overages round up; Worker estimates apply unit rates before currency display rounding.",
        ],
        "excluded": ["Workers base subscription, taxes/credits", "D1", "Durable Objects", "Queues",
                     "Workers Logs and other observability", "WAF/CDN paid options", "other account workloads",
                     "unmodeled R2 operations", "initial browser reads or retries not already included in public_reads"],
        "sources": prices["sources"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON scenario with explicit account prior usage and monthly allowance")
    parser.add_argument("--prices", type=Path, default=PRICING, help="Reviewed official rate snapshot")
    args = parser.parse_args()
    try:
        result = estimate(json.loads(args.input.read_text()), json.loads(args.prices.read_text()))
    except (ValueError, KeyError, OSError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
