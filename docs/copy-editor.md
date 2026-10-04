# Copy-editor and outputs

Docling converts one page at a time. A Deep Agents agent sees Docling's Markdown,
the page image, source headers/footers and links, plus the previous page tail
and continuity note as context. It submits text through one `submit_page` tool.
Prompts ask it to patch clearly visible errors and preserve the page's own text.
Filesystem, execution and general-purpose subagent tools are hidden.

The pipeline does not grade, clean up or retry completed model text. A missing
submission retains Docling's output and records a note. Transport failures can
retain Docling text; two consecutive failed batches disable later copy-editing.
These fallbacks do not establish accuracy.

Page notes feed one final text-only `submit_brief` call for the brief and index.
Single images use their page note as a caption. Inputs without page images skip
copy-editing; with AI enabled they can still receive a brief.
Reports record the selected model, reasoning, token usage and estimated cost.

`report.md` has YAML front-matter and invisible `<!-- page: N -->` anchors
(`slide` for decks). AI changes receive `<!-- ai-edited: … -->` labels.
Descriptions use `> **AI-generated description:**`; speaker notes use
`**Speaker notes:**`. Page files include previous/next filenames and page numbers.
Tables with spanning cells can be HTML, with linked screenshots for checking.

| Profile | Image scale | Tables | Formulas | Code | Scan OCR |
|---|---|---|---|---|---|
| low | 1.0 | fast | off | off | Docling default |
| medium | 1.5 | accurate | off | off | 300 DPI |
| high | 2.0 | accurate | on | off | 300 DPI |
| max | 3.0 | accurate | on | on | 300 DPI |

All profiles produce page/picture images. Medium/high/max also provide sharper
scan table crops. Formula inference is expensive on CPU. Docker uses RapidOCR;
native macOS can use Apple Vision. Large batches retain more page images.

## Models

Provider details stay in [everymd/models.py](../everymd/models.py). The default
is `openai:gpt-6-luna`, production reasoning `medium`; development uses `low`.
Settings are read when the model is built:

| Setting | Purpose |
|---|---|
| `EVERYMD_MODEL=provider:model` | Select a LangChain-supported provider/model |
| `EVERYMD_REASONING_EFFORT=low` | Match the measured Luna sample runs |
| `EVERYMD_BASE_URL=http://host:8000/v1` | OpenAI-compatible endpoint |
| `EVERYMD_API_KEY` | Key for a compatible endpoint, when needed |
| `EVERYMD_MODEL_SEES_IMAGES=false` | Structure-only editing for a text-only model |

OpenAI, Anthropic and Google packages are installed. Other providers need their
LangChain integration; rebuild Docker after adding its dependency. The model
must support tool calling. Vision is needed to check page images.
Alternatively pass `model="provider:model"` or a LangChain chat model to
`convert()`. No alternative provider is validated by this release task.

Deep Agents profiles are registered per process/model. Keep everymd in a separate
process from another Deep Agents application using the same model.
Unknown model prices produce an unknown estimate, not a zero-cost claim.
