---
title: "Setting up a garden moisture sensor"
source: "samples/inputs/page.html"
detected_type: "html"
resolution: "high"
ai_model: "gpt-6-luna"
page: 2
pages: 2
full_document: "page.md"
previous: "page.p0001.md"
next: null
ai_copy_edited: true
ai_continuity_note: "Where I am: ## Reading the sensor. Still open: None. Watch for: None."
ai_page_note: "Completes the Python code for reading the sensor and gives the watering rule: water the bed when the value stays below 20% for an hour."
---

<!-- page: 2 -->

```python
print(moisture(read_adc()))
time.sleep(600)
```

Water the bed when the value stays below 20% for an hour.

<!-- ai-edited: Restored the code block structure and line break visible in the image.; Removed the site footer. -->
