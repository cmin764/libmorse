"""Bidirectional morse signal interpreter and translator."""


import abc
import collections
import itertools
import threading
from Queue import Queue

import six
from scipy.cluster.vq import kmeans2

from libmorse import exceptions, morse, settings
from libmorse.utils import Logger


@six.add_metaclass(abc.ABCMeta)
class BaseTranslator(Logger):

    """Base class for any kind of translator"""

    CLOSE_SENTINEL = None
    CONFIG = {
        "signals": {
            "type": "signals",
            "means": 2,
            "mean_min_diff": settings.MEAN_MIN_DIFF,
            "min_length": settings.SIGNAL_RANGE[0],
            "ratios": {
                morse.DOT: 1.0,
                morse.DASH: 3.0,
            },
            "offset": 0,
        },
    }

    def __init__(self, *args, **kwargs):
        super(BaseTranslator, self).__init__(*args, **kwargs)

        self._input_queue = Queue()
        self._output_queue = Queue()
        self._closed = threading.Event()

        self._start()    # start the item processor

    def _free(self):
        pass

    @abc.abstractmethod
    def _process(self, item):
        pass

    def _run(self):
        while True:
            item = self._input_queue.get()
            self._input_queue.task_done()
            if item == self.CLOSE_SENTINEL:
                self._closed.set()
                self._free()
                break
            results = self._process(item)
            if not isinstance(results, (tuple, list, set)):
                results = [results]
            for result in results:
                if result != self.CLOSE_SENTINEL:
                    # Add rightful results only.
                    self._output_queue.put(result)

    def _start(self):
        thread = threading.Thread(target=self._run)
        thread.setDaemon(True)
        thread.start()

    def put(self, item):
        """Add a new item to the processing queue.

        This can be a simple alphabet letter or timed signal.
        """
        if self.closed:
            if item == self.CLOSE_SENTINEL:
                raise exceptions.TranslatorMorseError(
                    "translator already closed"
                )
            raise exceptions.TranslatorMorseError(
                "put operation on closed translator"
            )
        self._input_queue.put(item)

    def get(self):
        """Retrieve and return from the processed items a new item."""
        if self.closed:
            raise exceptions.TranslatorMorseError(
                "get operation on closed translator"
            )
        result = self._output_queue.get()
        self._output_queue.task_done()
        return result

    @property
    def closed(self):
        """Returns True if the translator is closed."""
        return self._closed.is_set()

    def close(self):
        """Close the translator and free resources."""
        self.put(self.CLOSE_SENTINEL)


class AlphabetTranslator(BaseTranslator):

    """Alphabet to morse translator."""


class MorseTranslator(BaseTranslator):

    """Morse to alphabet translator."""

    def __init__(self, *args, **kwargs):
        super(MorseTranslator, self).__init__(*args, **kwargs)

        # Actively analysed signals.
        self._signals = collections.deque(settings.SIGNAL_RANGE[1])
        # Actively analysed silences; the same range may work.
        self._silences = collections.deque(settings.SIGNAL_RANGE[1])
        # First and last provided items.
        self._begin = None
        self._last = None
        # Actual morse code, divided and combined.
        self._morse_signals = []
        self._morse_silences = []
        self._morse_code = []

    def _free(self):
        super(MorseTranslator, self)._free()
        self._signals.clear()
        self._silences.clear()

    @classmethod
    def _get_signal_classes(cls, means, ratios):
        """Classify the means into signal types."""
        classes = []
        unit = min(means)

        for mean in means:
            ratio = mean / unit
            # Find closest defined ratio.
            best_class = None
            min_delta = abs(ratios.items()[0][1] - ratio) + 1
            for entity, entity_ratio in ratios.items():
                delta = abs(ratio - entity_ratio)
                if delta < min_delta:
                    min_delta = delta
                    best_class = entity
            classes.append(best_class)

        return classes

    def _analyse(self, container, config):
        """Analyse and translate if possible the current range of
        signals or silences.
        """
        # Get a first classification of the signals.
        means, distribution = kmeans2(container, config["means"])
        unit = min(means)
        limit = config["mean_min_diff"] * unit
        for combi in itertools.combinations(means, 2):
            delta = abs(combi[0] - combi[1])
            if delta < limit:
                # Insufficient signals.
                return None

        # We've got a correct distribution. Take each remaining unprocessed
        # signal and normalize its classification.
        signal_classes = self._get_signal_classes(means, config["ratios"])
        signals = []
        for signal_index in distribution[config["offset"]:]:
            signals.append(signal_classes[signal_index])
        config["offset"] = len(distribution)
        return signals

    def _parse_morse_code(self):
        """Transform obtained morse code into alphabet."""
        return self._morse_code

    def _process(self, item):
        if not self._begin:
            # Used for knowing how to bounce between the signals.
            self._begin = item
        # Decide active container depending on the signal type.
        if item[0]:
            container = self._signals
            selected = "signals"
        else:
            container = self._silences
            selected = "silences"
        config = self.CONFIG[selected]
        # Take the last saved item and join with the new one if it's from the
        # same kind, otherwise just add the new one.
        if self._last and item[0] == self._last[0]:
            # Join durations.
            item = (item[0], item[1] + self._last[1])
            container[-1] = item[1]
        else:
            # Before appending, adjust the offset according to queue fullness.
            if len(container) >= container.maxlen:
                if config["offset"] <= 0:
                    raise exceptions.TranslatorMorseError(
                        "insufficient {}".format(selected))
                config["offset"] -= 1
            # Add a new signal (duration only).
            container.append(item[1])
        self._last = item

        # Re-process the new state of the active queues and try to give a
        # result based on the current set of signals and silences.
        pairs = [
            (self._signals, self.CONFIG["signals"], self._morse_signals),
            (self._silences, self.CONFIG["silences"], self._morse_silences)
        ]
        for container, config, collection in pairs:
            if len(container) >= config["min_length"]:
                signals = self._analyse(container, config)
                collection.extend(signals or [])

        # Combine obtained morse signals and silences.
        sig, sil = self._morse_signals, self._morse_silences
        sets = [sig, sil]
        if all(sets):
            # We have items from both.
            if not self._begin[0]:
                # Starting with a silence first.
                sets = [sil, sig]
            # Just merge them sequentially.
            merged = [item for pair in zip(sets) for item in pair]
            self._morse_code.extend(merged)
            # Then discard the mixed items.
            idx = min([len(collection) for collection in sets])
            del sig[:idx]
            del sil[:idx]

            # Parse actual morse code and send the result
            # for the output queue.
            return self._parse_morse_code()

        return self.CLOSE_SENTINEL    # nothing obtained yet
