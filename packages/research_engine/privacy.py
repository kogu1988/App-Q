import re

# Standard regex patterns for PII
PII_PATTERNS = {
    "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "PHONE": r"(?:\+90|0)?\s?[5]\d{2}\s?\d{3}\s?\d{2}\s?\d{2}", # TR phone number format
    "TC_ID": r"\b[1-9][0-9]{10}\b" # TR ID card format
}

class PrivacyMasker:
    """Masks PII and custom restricted words from text before sending to LLM."""
    
    def __init__(self, custom_keywords: list[str] | None = None):
        self.custom_keywords = [k.strip() for k in (custom_keywords or []) if len(k.strip()) > 2]
        self._reverse_map: dict[str, str] = {}
        self._mask_counter = 1
        
    def _generate_placeholder(self, category: str) -> str:
        placeholder = f"[{category}_{self._mask_counter}]"
        self._mask_counter += 1
        return placeholder

    def mask(self, text: str) -> str:
        masked_text = text
        
        # 1. Mask Custom Keywords (exact, case-insensitive match)
        for keyword in self.custom_keywords:
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            def custom_repl(match):
                original = match.group(0)
                # Check if we already mapped this exact string
                for ph, orig in self._reverse_map.items():
                    if orig.lower() == original.lower():
                        return ph
                ph = self._generate_placeholder("RESTRICTED")
                self._reverse_map[ph] = original
                return ph
            masked_text = pattern.sub(custom_repl, masked_text)

        # 2. Mask PII Patterns
        for category, pattern in PII_PATTERNS.items():
            compiled_pattern = re.compile(pattern)
            def pii_repl(match):
                original = match.group(0)
                # Check if already mapped
                for ph, orig in self._reverse_map.items():
                    if orig == original:
                        return ph
                ph = self._generate_placeholder(category)
                self._reverse_map[ph] = original
                return ph
            masked_text = compiled_pattern.sub(pii_repl, masked_text)
            
        return masked_text

    def unmask(self, text: str) -> str:
        unmasked = text
        # Sort by length descending to prevent partial replacement if placeholders overlap
        for ph, original in sorted(self._reverse_map.items(), key=lambda x: len(x[0]), reverse=True):
            unmasked = unmasked.replace(ph, original)
        return unmasked


class PrivacyResearchModelWrapper:
    """Wraps any ResearchModel to apply privacy masking to prompts and unmasking to responses."""

    def __init__(self, model, masker: PrivacyMasker):
        self._model = model
        self.masker = masker

    @property
    def last_model_id(self):
        return getattr(self._model, "last_model_id", None)

    def generate(self, system: str, prompt: str) -> str:
        masked_system = self.masker.mask(system)
        masked_prompt = self.masker.mask(prompt)
        response = self._model.generate(masked_system, masked_prompt)
        return self.masker.unmask(response)

    def generate_stream(self, system: str, prompt: str):
        masked_system = self.masker.mask(system)
        masked_prompt = self.masker.mask(prompt)
        
        # We need to unmask the stream chunks. This is tricky because placeholders might be split across chunks.
        # For simplicity, we assume placeholders are sent entirely, or we just unmask full text at the UI level.
        # But wait, LLM will generate placeholders like [PHONE_1]. We can just unmask them.
        buffer = ""
        for chunk in self._model.generate_stream(masked_system, masked_prompt):
            buffer += chunk
            # Check if there is an unclosed bracket that might be a placeholder
            if "[" in buffer and "]" not in buffer[buffer.rfind("["):]:
                continue # Wait for more chunks
                
            # If we have a full string without unclosed brackets, we can yield unmasked
            unmasked_buffer = self.masker.unmask(buffer)
            yield unmasked_buffer
            buffer = ""
            
        if buffer:
            yield self.masker.unmask(buffer)

