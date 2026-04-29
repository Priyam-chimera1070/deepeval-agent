"""
Full API test — requires server to be running.
Run server first: .\\venv\\Scripts\\activate.ps1; py run.py
Then in another terminal: .\\venv\\Scripts\\activate.ps1; py test_api.py
"""
import requests

BASE_URL = "http://localhost:8000"


def _print_response(result):
    print(f"Evaluation ID: {result['evaluation_id']}")
    print(f"Agent: {result['agent_name']}")
    print(
        f"Average Score: {result['average_score']}% | Status: {result['average_status']} | "
        f"Successful: {result['successful_runs']}/{result['total_runs']} | Failed: {result['failed_runs']}"
    )
    for run in result["runs"]:
        print(f"\n  Run: {run['run_id']} | Status: {run['status']}")
        if run['status'] == "ERROR":
            print(f"    Error: {run.get('error')}")
            continue
        print(f"    Query: {run['user_query'][:80]}...")
        print(f"    Metrics: {run['metrics']}")
        print(f"    Judge: score={run['judge_score']}% confidence={run['judge_confidence']}%")
        print(f"    Overall: {run['overall_score']}%")
        if run.get('judge_reasoning'):
            print(f"    Reasoning: {run['judge_reasoning'][:200]}...")
        if run.get('judge_strengths'):
            print(f"    Strengths: {run['judge_strengths']}")
        if run.get('judge_issues'):
            print(f"    Issues: {run['judge_issues']}")
        if run.get('judge_suggestions'):
            print(f"    Suggestions: {run['judge_suggestions']}")


def test_health():
    print("=== Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code} | Response: {response.json()}\n")


def test_single_run():
    print("=== Single Run Evaluation ===")
    payload = {
        "runs": [
            {
                "run_id": "run-001",
                "user_query": "Summarize the clinical trial results for Drug X",
                "input": "Summarize clinical trial results for Drug X for Medical Affairs",
                "output": """Key Insights: Drug X showed 45% reduction in primary endpoint.
Section 1: Overview - Drug X Phase 3 trial enrolled 1200 patients.
Section 2: Efficacy - Primary endpoint met with p<0.001.
Section 3: Safety - Well tolerated, 12% adverse events.
Section 4: Medical Affairs CCG - Full 3-column format: Indication | Evidence | Recommendation.
Section 5: Development Summary - Condensed pipeline status.
Section 6: Development CCG - Condensed format for pipeline team.
Section 7: Confidence - HIGH confidence based on Phase 3 data. MEDIUM for subgroup analysis. LOW for long-term outcomes.
Filters confirmed: Indication=Oncology, Phase=3, Role=Medical Affairs, Region=US, Year=2024."""
            }
        ]
    }

    response = requests.post(f"{BASE_URL}/evaluate", json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        _print_response(response.json())
    else:
        print(f"Error: {response.text}")
    print()


def test_multiple_runs():
    print("=== Multiple Runs Evaluation ===")
    payload = {
        "runs": [
            {
                "run_id": "run-001",
                "user_query": "What are the safety profiles for Drug Y?",
                "input": "Safety profile for Drug Y",
                "output": """Key Insights: Drug Y demonstrates favorable safety profile.
Section 1: Overview - Phase 2/3 safety data from 800 patients.
Section 2: Efficacy - Secondary safety endpoints all met.
Section 3: Safety - 8% serious adverse events, mostly manageable.
Section 4: Medical Affairs CCG - Indication: Cardiology | Evidence: Phase 3 | Recommendation: Monitor cardiac function.
Section 5: Development Summary - On track for regulatory submission.
Section 6: Development CCG - Timeline: Q2 2025 submission.
Section 7: Confidence - HIGH for primary safety, MEDIUM for rare events, LOW for pediatric use.
Filters: Indication=Cardiology, Phase=2/3, Role=Medical Affairs, Region=EU, Year=2024."""
            },
            {
                "run_id": "run-002",
                "user_query": "Long-term safety data for Drug Y",
                "input": "Long-term safety data for Drug Y",
                "output": """Key Insights: 2-year follow-up shows sustained safety.
Section 1: Overview - Extension study with 500 patients.
Section 2: Efficacy - Maintained efficacy over 24 months.
Section 3: Safety - No new safety signals identified.
Section 4: Medical Affairs CCG - Indication: Cardiology | Evidence: Extension | Recommendation: Continue monitoring.
Section 5: Development Summary - Post-marketing surveillance ongoing.
Section 6: Development CCG - Real-world evidence collection in progress.
Section 7: Confidence - HIGH for 2-year data, MEDIUM for 5-year projections.
Filters: Indication=Cardiology, Phase=Extension, Role=Medical Affairs, Region=Global, Year=2024."""
            }
        ]
    }

    response = requests.post(f"{BASE_URL}/evaluate", json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        _print_response(response.json())
    else:
        print(f"Error: {response.text}")
    print()


if __name__ == "__main__":
    test_health()
    test_single_run()
    test_multiple_runs()
