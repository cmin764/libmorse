"""Bidirectional morse signal interpreter and translator."""


import abc
import collections
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
        return self._output_queue.get()

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
        self._signals = collections.deque(settings.SIGNAL_RANGE)
        # Actively analysed silences; the same range may work.
        self._silences = collections.deque(settings.SIGNAL_RANGE)
        # Last provided item.
        self._last = None

    def _free(self):
        super(MorseTranslator, self)._free()
        self._signals.clear()
        self._silences.clear()

    def _process(self, item):
        # Decide active container depending on the signal type.
        container = self._signals if item[0] else self._silences
        # Take the last saved item and join with the new one if it's from the
        # same kind, otherwise just add the new one.
        if self._last and item[0] == self._last[0]:
            # Join durations.
            compound = (item[0], item[1] + self._last[1])
            container[-1] = compound
        else:
            # Add a new signal.
            container.append(item)
        self._last = item
        # Re-process the new state of the active queues and try to give a
        # result based on the current set of signals and silences.
        pass
