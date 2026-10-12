"""
Specialist Agents for Agentic Intelligence Platform.
Defines role instructions, backstories, narrow capabilities, and LLM configuration for:
- Query Planner
- Semantic Discovery Worker
- Procedure Analyst
- Configuration Analyst (Conditional)
- Relationship Analyst (Conditional)
- Troubleshooting Analyst (Conditional)
- Evidence Auditor
- Answer Synthesizer
"""

import os
import logging
from typing import Optional
from crewai import Agent, LLM

logger = logging.getLogger("sap_rag.agentic.orchestration.agents")


def get_agentic_llm(model_override: Optional[str] = None) -> LLM:
    """Initialize CrewAI LLM pointing to Groq or Google Gemini."""
    groq_key = (os.getenv("GROQ_API_KEY") or "").strip()
    gemini_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    provider = os.getenv("LLM_PROVIDER", "").lower().strip()

    # Priority: If GROQ_API_KEY is configured (or requested via model/provider), use Groq
    use_groq = bool(groq_key) and (
        provider == "groq"
        or not gemini_key
        or "groq" in (model_override or "").lower()
        or os.getenv("USE_GROQ", "true").lower() in ("1", "true", "yes")
    )

    if use_groq:
        os.environ["GROQ_API_KEY"] = groq_key
        raw_model = model_override or os.getenv("GROQ_MODEL") or os.getenv("AGENTIC_MODEL", "qwen/qwen3.8-27b")
        if raw_model.startswith("groq/"):
            raw_model = raw_model[5:]

        # CrewAI parses 'openai/{model}' and sends '{model}' to base_url
        crew_model = f"openai/{raw_model}" if not raw_model.startswith("openai/") else raw_model
        logger.info(f"Initialized Agentic CrewAI LLM with Groq model '{raw_model}'")
        return LLM(
            model=crew_model,
            base_url="https://api.groq.com/openai/v1",
            api_key=groq_key,
            temperature=float(os.getenv("AGENTIC_LLM_TEMP", "0.1")),
            max_tokens=int(os.getenv("AGENTIC_LLM_MAX_TOKENS", "3000")),
            timeout=30
        )

    # Fallback to Google Gemini
    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key
        os.environ["GOOGLE_API_KEY"] = gemini_key

    if model_override:
        model_name = model_override
    else:
        raw_model = os.getenv("AGENTIC_MODEL", os.getenv("GEMINI_MODEL", "gemini-3.5-flash"))
        # Auto-map deprecated or quota-exhausted models to active gemini-3.5-flash
        if raw_model in ("gemini-2.5-flash", "gemini-3.8-flash", "gemini-1.5-flash", "gemini/gemini-2.5-flash", "gemini/gemini-3.8-flash"):
            model_name = "gemini-3.5-flash"
        else:
            model_name = raw_model

    provider_model = f"gemini/{model_name}" if not model_name.startswith("gemini/") else model_name
    return LLM(
        model=provider_model,
        api_key=gemini_key,
        temperature=float(os.getenv("AGENTIC_LLM_TEMP", "0.1")),
        max_tokens=int(os.getenv("AGENTIC_LLM_MAX_TOKENS", "3000")),
        timeout=30,
        num_retries=1
    )


class AgenticSpecialistsFactory:
    """
    Factory creating focused CrewAI specialist agents with narrow, testable responsibilities.
    """

    @classmethod
    def create_query_planner(cls, llm: Optional[LLM] = None) -> Agent:
        return Agent(
            role="SAP Utilities Query Planner",
            goal="Analyze the user's question, determine the intent (procedural, configuration, conceptual, troubleshooting, relationship), extract SAP technical entities, and formulate a minimal, bounded set of targeted subquestions.",
            backstory=(
                "You are an expert SAP Utilities enterprise architect. You understand IS-U data models, "
                "device management, billing, contract accounts (FI-CA), customer service, and master data. "
                "You break down complex questions into 1 to 3 crisp, independent subquestions to guide targeted retrieval."
            ),
            llm=llm or get_agentic_llm(),
            verbose=False,
            allow_delegation=False
        )

    @classmethod
    def create_semantic_discovery_worker(cls, llm: Optional[LLM] = None, tools: list = None) -> Agent:
        return Agent(
            role="SAP Utilities Semantic Discovery Worker",
            goal="Execute direct semantic searches over the SAP documentation corpus for assigned subquestions, acquiring high-quality source passages.",
            backstory=(
                "You are an authoritative information retrieval specialist for SAP documentation. "
                "You know how to query technical vector indexes accurately and retrieve grounded evidence."
            ),
            llm=llm or get_agentic_llm(),
            tools=tools or [],
            verbose=False,
            allow_delegation=False
        )

    @classmethod
    def create_procedure_analyst(cls, llm: Optional[LLM] = None) -> Agent:
        return Agent(
            role="SAP Utilities Procedure Analyst",
            goal="Analyze retrieved documentation to extract documented prerequisites, ordered procedural steps, transaction codes, expected outcomes, and procedural exceptions.",
            backstory=(
                "You are an SAP Utilities business process engineer. You scrutinize documentation to find "
                "exact sequential execution steps, required inputs, pre-conditions, and validation steps. "
                "You never assume or invent steps not explicitly backed by the provided documentation."
            ),
            llm=llm or get_agentic_llm(),
            verbose=False,
            allow_delegation=False
        )

    @classmethod
    def create_configuration_analyst(cls, llm: Optional[LLM] = None) -> Agent:
        return Agent(
            role="SAP Utilities Configuration Analyst",
            goal="Analyze retrieved documentation for configuration tables, IMG customizing paths, parameters, technical indicators, and system dependencies.",
            backstory=(
                "You are an SAP Utilities functional configurator. You identify exact customizing activities, "
                "control tables, posting parameters, and system object dependencies directly from documentation."
            ),
            llm=llm or get_agentic_llm(),
            verbose=False,
            allow_delegation=False
        )

    @classmethod
    def create_relationship_analyst(cls, llm: Optional[LLM] = None) -> Agent:
        return Agent(
            role="SAP Utilities Relationship Analyst",
            goal="Trace cross-document dependencies, master data object hierarchies (Business Partner -> Contract Account -> Contract -> Installation), and document linkages.",
            backstory=(
                "You specialize in SAP IS-U relational architectures and data structures. "
                "You map how different SAP functional modules and documents connect to each other."
            ),
            llm=llm or get_agentic_llm(),
            verbose=False,
            allow_delegation=False
        )

    @classmethod
    def create_troubleshooting_analyst(cls, llm: Optional[LLM] = None) -> Agent:
        return Agent(
            role="SAP Utilities Troubleshooting Analyst",
            goal="Identify error messages, diagnostic procedures, reversal methods, boundary conditions, and exception resolution steps from documentation.",
            backstory=(
                "You are an SAP support and maintenance specialist. You identify root causes, documented "
                "reversals, error logs, and exception handling protocols without inventing workarounds."
            ),
            llm=llm or get_agentic_llm(),
            verbose=False,
            allow_delegation=False
        )

    @classmethod
    def create_evidence_auditor(cls, llm: Optional[LLM] = None) -> Agent:
        return Agent(
            role="SAP Utilities Evidence Auditor",
            goal="Critically challenge claims, detect ungrounded statements, identify conflicting documentation, and verify whether subquestions have adequate supporting evidence.",
            backstory=(
                "You are an uncompromising technical auditor and compliance officer. "
                "You review technical findings against the raw source evidence. If a claim lacks exact documentation "
                "backing, or if two documents contradict each other, you flag it immediately."
            ),
            llm=llm or get_agentic_llm(),
            verbose=False,
            allow_delegation=False
        )

    @classmethod
    def create_answer_synthesizer(cls, llm: Optional[LLM] = None) -> Agent:
        return Agent(
            role="SAP Utilities Answer Synthesizer",
            goal="Synthesize a single, coherent, professional answer grounded exclusively in audited evidence, with precise numbered bracketed citations [1], [2], prerequisites, ordered steps, and honest gap disclosures.",
            backstory=(
                "You are the chief technical communicator for SAP enterprise solutions. "
                "You synthesize diverse specialist findings into a single seamless answer. "
                "You never concatenate separate agent reports; you weave them into a unified explanation. "
                "Every material fact is backed by a numbered bracket citation [1] pointing to authoritative SAP sources. "
                "If documentation is incomplete, you explicitly state what is not documented."
            ),
            llm=llm or get_agentic_llm(),
            verbose=False,
            allow_delegation=False
        )
