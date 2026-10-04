# 0011 The model is switchable from one file

Decided 2026-10-03. Everything about the AI model lives in `everymd/models.py`: the model name (`provider:model`, built with LangChain's `init_chat_model`), provider settings (reasoning effort for OpenAI), how page images are sent (OpenAI `image_url` with `detail`, LangChain's standard image block for other providers), which key each provider needs, whether the model sees images, and prices. It can be switched without code changes through `EVERYMD_MODEL`, `EVERYMD_BASE_URL` (any OpenAI-compatible server, including local open-source models), `EVERYMD_API_KEY` and `EVERYMD_MODEL_SEES_IMAGES` in `.env`. OpenAI, Anthropic and Google packages are already in the image; others need their LangChain package added and a rebuild.

Decision 0004 still holds for the default and for testing: the default stays `openai:gpt-6-luna`, and test runs use it at low reasoning. Other providers are built in offline tests but never called.

Approved by Arjun in Claude Code (voice dictation, quoted as transcribed): "currently it is fixed for OpenAI, but I want any model to be used here, any open source, any models can be used here from any provider ... if we only change that file, then everything everywhere, the model calling will, will be only dependent on that ... It should be like switchable".
