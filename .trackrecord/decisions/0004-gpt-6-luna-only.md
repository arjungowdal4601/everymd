# 0004 Copy-editor model: gpt-6-luna only; low reasoning for tests

Decided 2026-10-02. The copy-editor uses OpenAI `gpt-6-luna` and no other model. Test and development runs use reasoning effort `low`. The production default is the agent's choice: `medium` (Luna's own default), set in `everymd/config.py` and overridable with `EVERYMD_REASONING_EFFORT`.

Context: gpt-6-luna was the cheapest current vision model on 2026-10-02 ($0.10 in / $0.50 out per 1M tokens); gpt-6.1-sol was offered as the stronger, ~20x pricier alternative.

Approved by Arjun on 2026-10-02 in Claude Code, choosing "gpt-6-luna (Recommended)", and in his own words (voice dictation, quoted as transcribed): "So you have to use only GPT Luna 6 model. So this is the only model you have to use. So reasoning is your, your choice. You can use whatever reasoning you want. But for testing purpose, always use reasoning as low. Okay. For uh, for for production purpose, you can use any reasoning which you choose. Okay."
