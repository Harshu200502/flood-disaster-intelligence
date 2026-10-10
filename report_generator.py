
import json
import os

from dotenv import load_dotenv
from google import genai

from rag import build_index, retrieve

load_dotenv()


def retrieve_guidance(query, top_k=3):
    """Retrieve relevant passages from the knowledge base."""
    vectorizer, matrix, chunks = build_index()
    return retrieve(query, vectorizer, matrix, chunks, top_k=top_k)


def fallback_report(scenario_data, risk_result, guidance):
    """Provide a clearly labelled fallback if the LLM is unavailable."""
    evidence = [
        {
            "source": item["source"],
            "text": item["text"],
            "relevance_score": item["score"],
        }
        for item in guidance
    ]

    report = (
        "LLM NOT AVAILABLE — FALLBACK SUMMARY\n\n"
        f"Scenario data:\n"
        f"{json.dumps(scenario_data, indent=2, default=str)}\n\n"
        f"Risk-engine result:\n"
        f"{json.dumps(risk_result, indent=2, default=str)}\n\n"
        "Review the evidence below. Verify all findings against "
        "current official information before taking action."
    )

    return {
        "status": "fallback",
        "report": report,
        "evidence": evidence,
        "warning": (
            "This is not an AI-generated report or an official "
            "emergency alert."
        ),
    }


def generate_flood_report(
    scenario_data,
    risk_result,
    retrieved_guidance=None,
):
    """Generate a flood situation report grounded in retrieved evidence."""

    if retrieved_guidance is None:
        location = scenario_data.get("location", "the affected area")
        query = (
            f"Flood safety, evacuation and emergency response for {location}. "
            f"Risk information: {risk_result}"
        )
        retrieved_guidance = retrieve_guidance(query, top_k=3)

    evidence = [
        {
            "source": item["source"],
            "text": item["text"],
            "relevance_score": item["score"],
        }
        for item in retrieved_guidance
    ]

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return fallback_report(
            scenario_data, risk_result, retrieved_guidance
        )

    prompt = f"""
You are a flood-disaster decision-support assistant.

Write a concise situation report using only the scenario,
risk-engine result, and retrieved guidance supplied below.

Include:
1. Situation overview
2. Risk assessment
3. Recommended response priorities
4. Data gaps and uncertainty
5. Evidence sources
6. Disclaimer

Rules:
- Never invent measurements or affected population figures.
- Clearly identify missing or simulated data.
- Do not claim that historical data is live.
- Do not invent official evacuation orders.
- Treat retrieval scores as relevance indicators, not truth probabilities.
- Cite the supplied source filenames in the report.
- If evidence is insufficient, state that clearly.
- Recommendations must defer to current official instructions.
- State that the report is decision support, not an official alert.

SCENARIO:
{json.dumps(scenario_data, indent=2, default=str)}

RISK ENGINE RESULT:
{json.dumps(risk_result, indent=2, default=str)}

RETRIEVED GUIDANCE:
{json.dumps(evidence, indent=2, default=str)}
"""

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=prompt,
        )

        report_text = (response.text or "").strip()

        if not report_text:
            raise ValueError("Gemini returned an empty response.")

        return {
            "status": "llm_generated",
            "report": report_text,
            "evidence": evidence,
            "warning": (
                "AI-generated decision support. Verify against current "
                "official information and qualified responders."
            ),
        }


    except Exception as exc:
        result = fallback_report(
            scenario_data, risk_result, retrieved_guidance
        )
        result["warning"] += (
            f" API request failed: {type(exc).__name__}: {exc}"
        )
        return result

