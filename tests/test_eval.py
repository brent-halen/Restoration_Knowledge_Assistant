from src.eval import evaluate_offline


def test_evaluate_offline_returns_summary():
    summary = evaluate_offline()
    assert summary["mode"] == "offline"
    assert summary["scenario_count"] == 6
    assert summary["overall_score_pct"] > 0
    assert len(summary["results"]) == 6
