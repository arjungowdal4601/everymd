"""Switching the model from models.py or .env, offline: models are built but never called."""

import pytest
from PIL import Image

from conftest import ScriptedModel, done, submit
from everymd import convert, models


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ("EVERYMD_MODEL", "EVERYMD_BASE_URL", "EVERYMD_API_KEY", "EVERYMD_MODEL_SEES_IMAGES"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")


def test_default_is_gpt_6_luna_with_reasoning_effort(monkeypatch):
    monkeypatch.setenv("EVERYMD_REASONING_EFFORT", "low")
    llm = models.build()
    assert models.provider_of(llm) == "openai" and models.name_of(llm) == "gpt-6-luna"
    assert llm.reasoning_effort == "low"


def test_env_switches_the_model_without_code_changes(monkeypatch):
    monkeypatch.setenv("EVERYMD_MODEL", "openai:some-other-model")
    assert models.name_of(models.build()) == "some-other-model"


def test_names_split_into_provider_and_model():
    assert models.split("ollama:qwen3-vl:8b") == ("ollama", "qwen3-vl:8b")
    assert models.split("gpt-6-luna") == ("openai", "gpt-6-luna"), "a bare name is an OpenAI model, as before"


def test_openai_compatible_server_needs_no_openai_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY")
    monkeypatch.setenv("EVERYMD_MODEL", "openai:local-vision-model")
    monkeypatch.setenv("EVERYMD_BASE_URL", "http://localhost:8000/v1")
    llm = models.build()
    assert llm.openai_api_base == "http://localhost:8000/v1"
    assert llm.reasoning_effort is None, "reasoning effort is only sent to OpenAI itself"


def test_missing_key_for_another_provider_names_its_variable(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        models.build("anthropic:some-model")


def test_missing_provider_package_says_what_to_add():
    with pytest.raises(RuntimeError, match="needs its LangChain package"):
        models.build("ollama:some-model")  # langchain-ollama is not in the image


def test_anthropic_and_gemini_packages_are_already_in_the_image(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-not-real")
    assert models.provider_of(models.build("anthropic:some-model")) == "anthropic"
    assert models.provider_of(models.build("google_genai:some-model")) == "google_genai"


class OtherProviderModel(ScriptedModel):
    def _get_ls_params(self, **kwargs):
        return {"ls_provider": "ollama", "ls_model_name": self.model_name, "ls_model_type": "chat"}


def test_images_use_openai_detail_or_the_standard_block():
    image = Image.new("RGB", (50, 50), "white")
    openai_block = models.image_block(image, ScriptedModel(messages=iter([])))
    assert openai_block["type"] == "image_url" and openai_block["image_url"]["detail"] == "high"
    other = models.image_block(image, OtherProviderModel(messages=iter([])))
    assert other["type"] == "image" and other["mime_type"] == "image/png" and other["base64"]


def test_a_model_that_cannot_see_images_gets_text_only(inputs, tmp_path, scripted, monkeypatch):
    monkeypatch.setenv("EVERYMD_MODEL_SEES_IMAGES", "false")
    model = scripted(submit(1, "An invoice"), done())
    result = convert(inputs / "invoice.png", output_dir=tmp_path, resolution="low", model=model)
    human = next(m for m in model.seen_requests[0] if m.type == "human")
    assert result.report["copy_editor_input"] == "text only"
    assert not [block for block in human.content if block["type"] in ("image_url", "image")]
