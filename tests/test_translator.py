import random
import unittest

import mock
import numpy as np

import libmorse
from libmorse import settings


DEBUG = True
log = libmorse.get_logger(__name__, debug=DEBUG)


class TestMorseTranslator(unittest.TestCase):

    # Morse code resources.
    MORSE = {
        "basic.mor": [
            "-- --- .-. ... . / -.-. --- -.. .",
            "MORSE CODE"
        ],
        "basic_noise.mor": [
            "-- --- .-. ... . / -.-. --- -.. .",
            "MORSE CODE"
        ],
    }

    def setUp(self):
        self.translator = libmorse.MorseTranslator(debug=DEBUG)

    def tearDown(self):
        self.translator.close()

    def _send_mor_code(self, mor_code):
        for signal in mor_code:
            self.translator.put(signal)
        self.translator.wait()

    def _get_translation(self, mor_file, get_alphabet=True, morse_code=None):
        mor_code = morse_code or libmorse.get_mor_code(mor_file)
        if get_alphabet:
            self._send_mor_code(mor_code)
        else:
            with mock.patch("libmorse.translator.MorseTranslator."
                            "_parse_morse_code") as mock_parse:
                def parse():
                    code = self.translator._morse_code[:]
                    self.translator._morse_code = []
                    return code
                mock_parse.side_effect = parse
                self._send_mor_code(mor_code)

        results = []
        while True:
            try:
                result = self.translator.get(block=False)
            except libmorse.TranslatorMorseError as exc:
                log.debug(exc)
                break
            results.append(result)

        return results

    def _test_alphamorse(self, name, test_alphabet=True, morse_code=None,
                         message=None, expected=None):
        translation = self._get_translation(
            name,
            get_alphabet=test_alphabet,
            morse_code=morse_code
        )
        result = "".join(translation).strip()
        if not test_alphabet:
            result = result.strip(" /")

        if expected is None:
            expected = self.MORSE[name][int(test_alphabet)]
        args = [expected, result]
        if message:
            args.append(message)
        self.assertEqual(*args)

    def test_basic_morse(self):
        self._test_alphamorse("basic.mor", test_alphabet=False)

    def test_basic_alphabet(self):
        self._test_alphamorse("basic.mor", test_alphabet=True)

    def test_basic_noise_morse(self):
        self._test_alphamorse("basic_noise.mor", test_alphabet=False)

    def test_basic_noise_alphabet(self):
        self._test_alphamorse("basic_noise.mor", test_alphabet=True)

    def _test_no_silence_morse(self, message, remove_idx, expected=None):
        """Strip the beginning and ending silence."""
        mor_code = libmorse.get_mor_code("basic.mor")
        for idx in remove_idx:
            mor_code.pop(idx)
        self._test_alphamorse("basic.mor", morse_code=mor_code,
                              message=message, expected=expected)

    def test_no_silence_morse_begin(self):
        self._test_no_silence_morse(
            "no silence at beginning",
            [0]
        )

    def test_no_silence_morse_end(self):
        self._test_no_silence_morse(
            "no silence at the end",
            [-1],
            expected="MORSE COD"
        )

    def test_no_silence_morse_all(self):
        self._test_no_silence_morse(
            "no silence at all",
            [0, -1],
            expected="MORSE COD"
        )

    def test_mixed_signals(self):
        # Get two common morse codes.
        morse_codes = []
        code, noise_code = map(
            libmorse.get_mor_code, ["basic.mor", "basic_noise.mor"])
        # Make the test coherent.

        def adapt(a_code, safe=True):
            # Remove (by reducing to 1ms) the first silence in a code,
            # if exists.
            item = a_code[0]
            if not item[0]:
                item = (item[0], 1)
                a_code[0] = item
                if safe:
                    a_code.pop(0)
            return a_code

        code, noise_code = map(adapt, [code, noise_code])

        times = random.randint(4, 6)
        for _ in range(times):
            sel_code = random.choice([code, noise_code])
            morse_codes.extend(sel_code)
        expected = " ".join(["MORSE CODE"] * times)

        self._test_alphamorse(None, morse_code=morse_codes, expected=expected)

    def _test_stable_kmeans(self, clusters_dim, tests_dim=100):
        # Generate random signals that should be classified in `clusters_dim`
        # groups.
        unit = settings.UNIT
        ideal_means = [unit]
        for _ in range(clusters_dim - 1):
            ideal_means.append(ideal_means[-1] * 2 + unit)
        # Make a few tests with different data, but the very same labeling.
        for crt in range(tests_dim):
            # How many signals of each label.
            sig_dim = np.random.randint(*settings.SIGNAL_RANGE) / clusters_dim
            # The actual signals.
            signals = []
            for mean in ideal_means:
                dist = np.random.randn(sig_dim) * 10 + mean
                signals.extend(dist.tolist())
            # Run clustering.
            random.shuffle(signals)
            _, labels = self.translator._stable_kmeans(
                signals, clusters_dim)
            labels_list = labels.tolist()
            for idx in range(clusters_dim):
                self.assertEqual(sig_dim, labels_list.count(idx),
                                 "iteration #{}".format(crt + 1))

    def test_stable_kmeans_2_clusters(self):
        self._test_stable_kmeans(2)

    def test_stable_kmeans_3_clusters(self):
        self._test_stable_kmeans(3)
