import io
import array
import time
import requests
from talon import app, speech_system, Module, Context, settings
from talon.lib.cubeb import DeviceInfo
from talon.engines import AbstractEngine, EngineStatus
from talon.grammar import Grammar
from talon.lib import flac
from typing import Iterable, Optional, Sequence

def convert(samples: Sequence[float]):
    api_key = settings.get('user.elevenlabs_api_key')
    if not api_key:
        app.notify('no elevenlabs api key!')
        raise Exception('no elevenlabs api key!')

    data = flac.encode(samples)
    resp = requests.post(
        'https://api.elevenlabs.io/v1/speech-to-text',
        data={
            'model_id': 'scribe_v1',
            'tag_audio_events': False,
            'diarize': False,
        },
        files={
            'file': ('a.flac', data, 'audio/flac'),
        },
        headers={
            'xi-api-key': api_key,
        },
    )
    print(resp.json())
    resp.raise_for_status()
    return resp.json()['text']

class ScribeEngine(AbstractEngine):
    name = 'scribe'
    need_vad = True

    def __init__(self):
        self.id = 'ScribeEngine'

    def _on_audio_frame(self, samples: Sequence[float], ts: float = 0.0, *, pad: bool = False) -> None:
        text = convert(samples)
        if text == '': return
        text = text.lower().removesuffix('.').strip()
        words = text.split(' ')
        print(words)
        self.dispatch('phrase', {
            'phrase': words,
            'samples': samples,
        })

    def enable(self) -> None: pass
    def disable(self) -> None: pass
    def close(self) -> None: pass

    def status(self) -> EngineStatus:
        status = EngineStatus()
        status.ready = True
        return status

    def mimic(self, phrase: Sequence[str]) -> None: self.dispatch('phrase', {'phrase': phrase})
    def set_microphone(self, device: Optional[DeviceInfo]) -> None: pass
    def sync_grammar(self, grammar: Grammar) -> None: pass
    def unload_grammar(self, grammar: Grammar) -> None: pass
    def set_vocab(self, words: Iterable[str]) -> None: pass

scribe = ScribeEngine()
speech_system.add_engine(scribe)

mod = Module()
mod.mode('scribe')
mod.setting(
    "elevenlabs_api_key",
    type=str,
    default=None,
    desc="Elevenlabs API key for Scribe speech engine",
)

ctx = Context()
ctx.matches = '''
mode: user.scribe
and not mode: command
'''
ctx.settings = {
    'speech.engine': 'scribe',
}
