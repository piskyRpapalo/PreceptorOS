"""Synthetic boundary tests; actual native voice measurement is separate."""
import hashlib
import io
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
import wave

import voz_lectura as V


class NativeReading(unittest.TestCase):
    def test_invalid_requests_never_start_an_engine(self):
        with patch.object(V.subprocess, 'run') as run:
            for request in ({}, {'text':'test','engine':'other'},
                            {'text':'test','engine':'host-espeak-ng','extra':1},
                            {'text':'x'*961,'engine':'host-espeak-ng'},
                            {'text':'\x00','engine':'host-espeak-ng'}):
                with self.assertRaises(V.ReadingUnavailable): V.synthesize(request)
            run.assert_not_called()

    def test_hardware_switch_and_missing_engine_deny(self):
        with patch.object(V.silencio, 'apagado', return_value=True):
            with self.assertRaisesRegex(V.ReadingUnavailable,'hardware_declared_off'):
                V.synthesize({'text':'test','engine':'host-espeak-ng'})
        with patch.object(V.silencio,'apagado',return_value=False), patch.object(V.shutil,'which',return_value=None):
            with self.assertRaisesRegex(V.ReadingUnavailable,'unavailable'):
                V.synthesize({'text':'test','engine':'host-espeak-ng'})

    def test_fixture_wave_receipt_is_bound_to_text_and_audio(self):
        text='Synthetic test, not a model answer.'
        def synth(args, **kwargs):
            self.assertEqual(kwargs['input'],text.encode())
            self.assertNotIn('shell',kwargs)
            with wave.open(args[-1],'wb') as w:
                w.setnchannels(1);w.setsampwidth(2);w.setframerate(22050);w.writeframes(b'\0'*4410)
            return subprocess.CompletedProcess(args,0)
        with patch.object(V.silencio,'apagado',return_value=False),patch.object(V.shutil,'which',return_value='fixture-espeak'),patch.object(V.subprocess,'run',side_effect=synth):
            audio,receipt=V.synthesize({'text':text,'engine':'host-espeak-ng'})
        self.assertEqual(receipt['text_sha256'],hashlib.sha256(text.encode()).hexdigest())
        self.assertEqual(receipt['audio_sha256'],hashlib.sha256(audio).hexdigest())

    def test_timeout_denies_and_releases_the_synthesis_lock(self):
        with patch.object(V.silencio,'apagado',return_value=False),patch.object(V.shutil,'which',return_value='fixture-espeak'),patch.object(V.subprocess,'run',side_effect=subprocess.TimeoutExpired('fixture',15)):
            with self.assertRaises(V.ReadingUnavailable):V.synthesize({'text':'test','engine':'host-espeak-ng'})
        self.assertTrue(V._LOCK.acquire(blocking=False));V._LOCK.release()

    def test_browser_local_only_chunk_and_stop_cases(self):
        root=Path(__file__).resolve().parent
        result=subprocess.run(['node','--test','tests/native_voice_cases.cjs'],cwd=root,capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
