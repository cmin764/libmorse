"""Bidirectional morse signal interpreter and translator."""


import Queue
import abc
import collections
import copy
import itertools
import threading

import six
from scipy.cluster.vq import kmeans, vq, whiten

from libmorse import converter, exceptions, settings
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
                converter.DOT: 1.0,
                converter.DASH: 3.0,
            },
            "offset": 0,
        },
        "silences": {
            "type": "silences",
            "means": 3,
            "mean_min_diff": settings.MEAN_MIN_DIFF,
            "min_length": settings.SIGNAL_RANGE[0],
            "ratios": {
                converter.INTRA_GAP: 1.0,
                converter.SHORT_GAP: 3.0,
                converter.MEDIUM_GAP: 7.0,
            },
            "offset": 0,
        },
    }

    def __init__(self, *args, **kwargs):
        super(BaseTranslator, self).__init__(__name__, *args, **kwargs)

        self._input_queue = Queue.Queue()
        self._output_queue = Queue.Queue()
        self._queue_processor = None    # parallel thread handling processing
        self._closed = threading.Event()

        self.config = copy.deepcopy(self.CONFIG)
        self.unit = settings.UNIT    # average used unit length

        self._start()    # start the item processor

    def _free(self):
        del self._input_queue
        del self._output_queue

    @abc.abstractmethod
    def _process(self, item):
        """Returns a list of processed items as results."""

    def _run(self):
        while True:
            item = self._input_queue.get()
            if item == self.CLOSE_SENTINEL:
                self._input_queue.task_done()
                self._free()
                break

            if not self.closed:
                results = self._process(item)
                if not isinstance(results, (tuple, list, set)):
                    results = [results]
                for result in results:
                    if result != self.CLOSE_SENTINEL:
                        # Add rightful results only.
                        self._output_queue.put(result)

            self._input_queue.task_done()

    def _start(self):
        self._queue_processor = threading.Thread(target=self._run)
        self._queue_processor.setDaemon(True)
        self._queue_processor.start()

    def put(self, item, **kwargs):
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
        try:
            self._input_queue.put(item, **kwargs)
        except Queue.Full:
            raise exceptions.TranslatorMorseError("full queue")

    def get(self, **kwargs):
        """Retrieve and return from the processed items a new item."""
        if self.closed:
            raise exceptions.TranslatorMorseError(
                "get operation on closed translator"
            )
        try:
            result = self._output_queue.get(**kwargs)
        except Queue.Empty:
            raise exceptions.TranslatorMorseError("empty queue")
        self._output_queue.task_done()
        return result

    @property
    def closed(self):
        """Returns True if the translator is closed."""
        return self._closed.is_set()

    def close(self):
        """Close and wait the translator to finish and free resources."""
        self.put(self.CLOSE_SENTINEL)
        self._closed.set()
        self._queue_processor.join()

    def wait(self):
        """Block until all the items in the queue are processed."""
        self._input_queue.join()


class AlphabetTranslator(BaseTranslator):

    """Alphabet to morse translator."""

    def __init__(self, *args, **kwargs):
        self._converter = converter.AlphabetConverter(*args, **kwargs)
        # Use predefined ratios when creating timings.
        self._ratios = copy.deepcopy(self.CONFIG["signals"]["ratios"])
        self._ratios.update(self.CONFIG["silences"]["ratios"])

        super(AlphabetTranslator, self).__init__(*args, **kwargs)

    def _process(self, item):
        # Convert every new character into a morse letter.
        letters = self._converter.add([item])
        # Translate the obtained morse code into timed signals.
        signals = []

        for letter in letters:
            if letter in (converter.SHORT_GAP, converter.MEDIUM_GAP):
                # Create the silence for the gap between characters or words.
                silence = (False, self._ratios[letter] * self.unit)
                signals.append(silence)
                continue

            # We have a letter; properly add all the successive signals and
            # silences.
            silence = (False, converter.INTRA_GAP * self.unit)
            extend = [((True, self._ratios[symbol] * self.unit), silence)
                      for symbol in letter]
            extend = [signal for pair in extend for signal in pair]
            # There is no intra-gap at the end of the letter; short gap
            # follows explicitly.
            extend.pop(-1)
            signals.extend(extend)

        return signals

    def _free(self):
        self._converter.free()

        super(AlphabetTranslator, self)._free()


class MorseTranslator(BaseTranslator):

    """Morse to alphabet translator."""

    def __init__(self, *args, **kwargs):
        # Actively analysed signals.
        self._signals = collections.deque(maxlen=settings.SIGNAL_RANGE[1])
        # Actively analysed silences; the same range may work.
        self._silences = collections.deque(maxlen=settings.SIGNAL_RANGE[1])
        # First and last provided items.
        self._begin = None
        self._last = None
        # Actual morse code, divided and combined.
        self._morse_signals = []
        self._morse_silences = []
        self._morse_pick = itertools.cycle([
            self._morse_signals, self._morse_silences
        ])
        self._morse_selected = None
        self._morse_code = []
        # Code converter.
        self._converter = converter.MorseConverter(*args, **kwargs)

        super(MorseTranslator, self).__init__(*args, **kwargs)

    def _free(self):
        self._signals.clear()
        self._silences.clear()
        self._morse_signals = []
        self._morse_silences = []
        del self._morse_pick
        self._morse_selected = None
        self._morse_code = []
        self._converter.free()

        super(MorseTranslator, self)._free()

    def _get_signal_classes(self, means, ratios):
        """Classify the means into signal types."""
        classes = []
        self.unit = min(means)    # good unit for reference
        ratios_items = ratios.items()

        for mean in means:
            ratio = mean / self.unit
            # Find closest defined ratio.
            best_class = None
            min_delta = abs(ratios_items[0][1] - ratio) + 1
            for entity, entity_ratio in ratios_items:
                delta = abs(ratio - entity_ratio)
                if delta < min_delta:
                    min_delta = delta
                    best_class = entity
            classes.append(best_class)

        return classes

    def _stable_kmeans(self, container, clusters):
        # Normalize the elements to be clustered.
        factor = container[0]
        container = whiten(container)
        factor /= container[0]
        # Get the stable means.
        while True:
            means = kmeans(container, clusters)[0]
            # Obtain and return the labels along with the means.
            labels = vq(container, means)[0]
            # Check for empty clusters.
            labels_set = set(labels)
            clusters_set = set(range(clusters))
            if labels_set == clusters_set:
                break
            self.log.warning("Empty clusters (%d/%d).",
                             *map(len, [labels_set, clusters_set]))
        # Return the original means along the labels distribution.
        return means * factor, labels

    def _analyse(self, container, config):
        """Analyse and translate if possible the current range of
        signals or silences.
        """
        # Get a first classification of the signals.
        means, distribution = self._stable_kmeans(container, config["means"])
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
        text = self._converter.add(self._morse_code)
        self._morse_code = []
        if text is None:
            return None
        return list(text)

    def _process(self, item):
        if not self._begin:
            # Used for knowing how to bounce between the signals.
            self._begin = item
            if not self._begin[0]:
                # Starting with a silence first.
                next(self._morse_pick)
        # Decide active container depending on the signal type.
        if item[0]:
            container = self._signals
            selected = "signals"
        else:
            container = self._silences
            selected = "silences"
        config = self.config[selected]
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
                        "missing {} variation".format(selected)
                    )
                config["offset"] -= 1
            # Add a new signal (duration only).
            container.append(item[1])
        self._last = item

        # Re-process the new state of the active queues and try to give a
        # result based on the current set of signals and silences.
        pairs = [
            (self._signals, self.config["signals"], self._morse_signals),
            (self._silences, self.config["silences"], self._morse_silences)
        ]
        for container, config, collection in pairs:
            if len(container) >= config["min_length"]:
                signals = self._analyse(container, config)
                collection.extend(signals or [])

        # Combine obtained morse signals and silences.
        news = False
        while True:
            self._morse_selected = next(self._morse_pick)
            if not self._morse_selected:
                next(self._morse_pick)
                break
            item = self._morse_selected.pop(0)
            self._morse_code.append(item)
            news = True

        # Parse the actual morse code and send the result for the output
        # queue if applicable.
        return self._parse_morse_code() if news else self.CLOSE_SENTINEL
