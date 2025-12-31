# Strict Domain-Restricted Answering Logic

## Overview

This document describes the strict domain-restricted answering logic implemented for the chatbot. The chatbot **NEVER** gives general AI answers and **ONLY** answers from:

1. Internal Knowledge Base (KB database)
2. Website content ingested from approved URLs

## Key Features

### 1. Enhanced Text Normalization

**Location**: `app/services/retrieval.py`

- **Persian Character Normalization**: Converts Arabic characters to Persian equivalents:
  - `ي` → `ی` (Arabic Yeh → Persian Yeh)
  - `ك` → `ک` (Arabic Kaf → Persian Kaf)
  - `ة` → `ه` (Arabic Teh Marbuta → Heh)
  - And more...

- **Comprehensive Normalization**:
  - Lowercase conversion
  - Whitespace normalization
  - Punctuation removal
  - Unicode normalization (NFD → NFC)

### 2. Advanced Similarity Matching

**Location**: `app/services/retrieval.py`

Uses multiple similarity metrics:
- **Token-based Jaccard similarity** (40% weight)
- **Trigram Jaccard similarity** (30% weight) - catches paraphrases
- **Substring matching** (20% weight)
- **Token overlap ratio** (10% weight)

This allows matching of paraphrased questions:
- Stored: "ساعات کاری شرکت چیست؟"
- User: "چه ساعتی کار می‌کنید؟"
- → Can match if similarity >= threshold

### 3. Strict Confidence Threshold

**Location**: `app/core/config.py`

- **Default threshold**: `0.70` (70% similarity required)
- Configurable via `MIN_CONFIDENCE_SCORE` environment variable
- Only answers if similarity score >= threshold

### 4. Hard Answer Guard

**Location**: `app/services/answer_guard.py` and `app/routers/chat.py`

**STRICT RULES**:
- If `kb_matches == empty AND website_matches == empty` → **DO NOT CALL OpenAI**
- If `max_confidence < MIN_CONFIDENCE_SCORE` → **DO NOT CALL OpenAI**
- Returns refusal with detailed reason

**Refusal Reasons**:
- `NO_MATCHING_SOURCE`: No results found
- `LOW_CONFIDENCE_X.XX_BELOW_0.70`: Similarity below threshold

### 5. Strict LLM System Prompt

**Location**: `app/services/llm.py`

The system prompt enforces:
- Answer **ONLY** using provided context
- If answer not in context → say "این اطلاعات در پایگاه دانش من وجود ندارد."
- **NO** general knowledge
- **NO** assumptions
- **NO** additional explanations

### 6. Enhanced Answer Validation

**Location**: `app/services/llm.py`

Post-processing validation:
- Requires at least 20% word overlap with context
- Requires at least 2 words from context in answer
- Rejects generic/hallucinated answers

### 7. Comprehensive Logging

**Location**: `app/routers/chat.py`

All refusals are logged with:
- `refusal_reason`: Detailed reason code
- `max_confidence`: Highest similarity score found
- `threshold`: Current threshold value
- `kb_results`: Number of KB matches
- `website_results`: Number of website matches
- `openai_called`: Always `false` for refusals

## Flow Diagram

```
User Question
    ↓
Normalize Text (Persian chars, lowercase, etc.)
    ↓
Retrieve from KB (fuzzy similarity)
    ↓
Has KB matches with score >= 0.70?
    ├─ YES → Use KB context → Call OpenAI → Return answer
    └─ NO  → Retrieve from Website (fuzzy similarity)
            ↓
            Has Website matches with score >= 0.70?
            ├─ YES → Use Website context → Call OpenAI → Return answer
            └─ NO  → REFUSE (DO NOT CALL OpenAI)
                    ↓
                    Return: {
                        "refused": true,
                        "answer": "این اطلاعات در پایگاه دانش من وجود ندارد.",
                        "openai_called": false,
                        "reason": "NO_MATCHING_SOURCE" or "LOW_CONFIDENCE_..."
                    }
```

## Configuration

### Environment Variables

```bash
# Strict confidence threshold (default: 0.70)
MIN_CONFIDENCE_SCORE=0.70

# Number of top KB results to retrieve
KB_TOP_K=5

# Number of top website results to retrieve
WEBSITE_TOP_K=3
```

### Adjusting Strictness

To make the bot **more strict** (fewer false positives):
- Increase `MIN_CONFIDENCE_SCORE` (e.g., `0.80` or `0.90`)

To make the bot **less strict** (more matches):
- Decrease `MIN_CONFIDENCE_SCORE` (e.g., `0.60` or `0.50`)
- **Warning**: Lower thresholds may allow answers that aren't truly relevant

## Testing

### Test Files

1. **`test_strict_domain_restriction.py`**: Comprehensive tests for:
   - Similar question wording matching
   - General question refusal
   - Website-only answers
   - OpenAI never called on refusal
   - Low confidence refusal
   - Persian normalization

2. **`test_chat_refusal.py`**: Tests for refusal scenarios

3. **`test_chat_with_sources.py`**: Tests for successful answer generation

### Running Tests

```bash
cd apps/backend
pytest tests/test_strict_domain_restriction.py -v
pytest tests/test_chat_refusal.py -v
pytest tests/test_chat_with_sources.py -v
```

## Key Guarantees

✅ **OpenAI is NEVER called** when no matches found  
✅ **OpenAI is NEVER called** when confidence < threshold  
✅ **Only answers from KB or Website** - no general knowledge  
✅ **Paraphrased questions can match** via fuzzy similarity  
✅ **Persian character variants normalized** (ي/ی, ك/ک)  
✅ **Detailed refusal reasons** logged for debugging  
✅ **Strict validation** prevents hallucination  

## Example Scenarios

### Scenario 1: Exact Match
- **KB**: "ساعات کاری شرکت چیست؟" → "9 صبح تا 6 عصر"
- **User**: "ساعات کاری شرکت چیست؟"
- **Result**: ✅ Matches (score ~1.0) → Answers

### Scenario 2: Paraphrased Match
- **KB**: "ساعات کاری شرکت چیست؟" → "9 صبح تا 6 عصر"
- **User**: "چه ساعتی کار می‌کنید؟"
- **Result**: ✅ May match (score depends on similarity) → Answers if >= 0.70

### Scenario 3: General Question
- **KB**: Empty or unrelated
- **User**: "بهترین گوشی 2025 چیه؟"
- **Result**: ❌ Refused → `openai_called=false`, `refused=true`

### Scenario 4: Low Similarity
- **KB**: "ساعات کاری شرکت چیست؟" → "9 صبح تا 6 عصر"
- **User**: "سلام"
- **Result**: ❌ Refused (similarity < 0.70) → `openai_called=false`

## Migration Notes

### Breaking Changes

1. **Default threshold changed**: `0.3` → `0.70`
   - Previously answered questions may now be refused
   - Adjust `MIN_CONFIDENCE_SCORE` in `.env` if needed

2. **Refusal message**: Shows "پاسخی برای این سوال ندارم" when no answer is available
   - Previously was "این اطلاعات در پایگاه دانش من وجود ندارد."
   - Message "از مدیر بخواهید این سوال را اضافه کند" has been removed

3. **Stricter validation**: Answers must have 20% word overlap with context (was 10%)

### Backward Compatibility

- All existing KB items work the same
- Website sources work the same
- API response format unchanged (just stricter logic)

## Troubleshooting

### Question: "Why is my question being refused even though it's similar?"

**Answer**: Check the similarity score:
1. Look at logs for `max_confidence` value
2. If < 0.70, it will be refused
3. Options:
   - Add more similar wording to KB
   - Lower `MIN_CONFIDENCE_SCORE` (not recommended)
   - Improve question wording to match KB better

### Question: "Can I disable strict mode?"

**Answer**: No. This is a core requirement. However, you can:
- Lower `MIN_CONFIDENCE_SCORE` to 0.60 or 0.50 (less strict)
- Add more KB items with varied wording
- Ensure website sources are enabled and crawled

### Question: "How do I know if OpenAI was called?"

**Answer**: Check the response:
- `"openai_called": true` → OpenAI was called
- `"openai_called": false` → OpenAI was NOT called (refused)

## Future Enhancements

Potential improvements (not implemented):
- Semantic embeddings (e.g., sentence transformers) for better matching
- Configurable similarity algorithm weights
- Per-source confidence thresholds
- A/B testing different thresholds

