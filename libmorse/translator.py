"""Bidirectional morse signal interpreter and translator."""


import abc
import collections
import itertools
import threading
from Queue import Queue

import six
from scipy.cluster.vq import kmeans2

from libmorse import exceptions, settings
from libmorse.utils import Logger


@six.add_metaclass(abc.ABCMeta)
class BaseTranslator(Logger):

    """Base class for any kind of translator"""

    CLOSE_SENTINEL = None

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
            result = self._process(item)
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

    CONFIG = {
        "signals": {
            "type": "signals",
            "means": 2,
            "mean_min_diff": settings.MEAN_MIN_DIFF,
            "min_length": settings.SIGNAL_RANGE[0],
        },
    }

    DOT = "."
    DASH = "-"

    def __init__(self, *args, **kwargs):
        super(MorseTranslator, self).__init__(*args, **kwargs)

        # Actively analysed signals.
        self._signals = collections.deque(settings.SIGNAL_RANGE[1])
        # Actively analysed silences; the same range may work.
        self._silences = collections.deque(settings.SIGNAL_RANGE[1])
        # First and last provided items.
        self._first = None
        self._last = None
        # First non-processed offset in the queues.
        self._signals_offset = 0
        self._silences_offset = 0

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
            # Find closes defined ratio.
            best_entity = None
            min_delta = abs(ratios.items()[0][1] - ratio) + 1
            for entity, entity_ratio in ratios.items():
                delta = abs(ratio - entity_ratio)

        return classes

    def _analyse(self, container, config):
        """Analyse and translate if possible the current range of
        signals or silences.
        """
        # Get a first classification of the signals.
        means, distribution = kmeans2(container, config["means"])
        unit = min(means)
        for combi in itertools.combinations(means, 2):
            delta = abs(combi[0] - combi[1])
            limit = config["mean_min_diff"] * unit
            if delta < limit:
                return    # no sufficient signals

        # We've got a correct distribution. Take each remaining unprocessed
        # signal and normalize its classification.
        signal_classes = self._get_signal_classes(means, config["ratios"])
        for signal in distribution[config["offset"]:]:

    def _process(self, item):
        if not self._first:
            # Used for knowing how to bounce between the signals.
            self._first = item
        # Decide active container depending on the signal type.
        container = self._signals if item[0] else self._silences
        # Take the last saved item and join with the new one if it's from the
        # same kind, otherwise just add the new one.
        if self._last and item[0] == self._last[0]:
            # Join durations.
            item = (item[0], item[1] + self._last[1])
            container[-1] = item[1]
        else:
            # Add a new signal (duration only).
            container.append(item[1])
        self._last = item

        # Re-process the new state of the active queues and try to give a
        # result based on the current set of signals and silences.

        # For the signals first.
        container = self._signals
        config = self.CONFIG["signals"]
        if len(container) >= config["min_length"]:
            self._analyse(container, config)

        # And also for the silences.
        pass ####
