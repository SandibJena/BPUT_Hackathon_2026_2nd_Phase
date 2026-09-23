class LLMProvider:
    def extract_triage_info(self, text):
        raise NotImplementedError()

class ClaudeProvider(LLMProvider):
    def extract_triage_info(self, text):
        return {}

def get_provider():
    return ClaudeProvider()
