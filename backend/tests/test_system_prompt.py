from app.knowledge.system_prompt import build_system_prompt, load_knowledge


def test_knowledge_file_loads_and_is_substantial():
    knowledge = load_knowledge()
    assert len(knowledge) > 500


def test_prompt_contains_required_knowledge_fragments():
    prompt = build_system_prompt()

    # Core facts a real user is likely to ask about (challenge brief scenarios)
    assert "AI Strategy" in prompt
    assert "AI Maturity Index" in prompt
    assert "eight-pillar" in prompt
    assert "Cadre portal" in prompt
    assert "hello@gocadre.ai" in prompt
    assert "Professional Services" in prompt
    assert "Financial Services" in prompt


def test_prompt_marks_unpublished_facts_explicitly():
    prompt = build_system_prompt()

    # Pricing and certifications must be explicitly flagged as unpublished,
    # not silently absent (which would invite the model to guess).
    assert "Not published" in prompt or "not published" in prompt
    assert "No certifications found" in prompt


def test_prompt_instructs_grounding_and_escalation():
    prompt = build_system_prompt()

    assert "escalate" in prompt.lower()
    assert "only" in prompt.lower()
    assert "never guess" in prompt.lower() or "do not use outside knowledge" in prompt.lower()


def test_prompt_forbids_inventing_sensitive_claims():
    prompt = build_system_prompt()

    lowered = prompt.lower()
    assert "certification" in lowered
    assert "case study result" in lowered or "case study" in lowered
    assert "specific price" in lowered or "pricing" in lowered


def test_prompt_treats_escalation_as_non_failure():
    prompt = build_system_prompt()
    lowered = prompt.lower()

    # The core Phase 1 review fix: escalate=true must not be framed as an
    # error, and "not published" answers should be confident, not apologetic.
    assert "not a failure signal" in lowered
    assert "never apologize" in lowered or "not sound uncertain" in lowered or "sound uncertain" in lowered
    assert "hello@gocadre.ai" in prompt
    assert "escalate: false" in lowered
