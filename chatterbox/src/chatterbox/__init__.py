try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version  # For Python <3.8

try:
    __version__ = version("chatterbox-tts")
except Exception:
    # Fallback when package metadata is not available (e.g., path-based import)
    __version__ = "1.0.0"


from .tts import ChatterboxTTS
from .vc import ChatterboxVC
from .mtl_tts import ChatterboxMultilingualTTS, SUPPORTED_LANGUAGES
from .tts_turbo import ChatterboxTurboTTS
from .mtl_tts import ChatterboxMultilingualTTS, SUPPORTED_LANGUAGES