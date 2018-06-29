from osc_message import OscMessage
from osc_types import get_date, get_int

_BUNDLE_PREFIX = b"#bundle\x00"


class ParseError(Exception):
    pass


class OscBundle(object):
    """Bundles elements that should be triggered at the same time.

    An element can be another OscBundle or an OscMessage.
    """

    def __init__(self, dgram):
        """Initializes the OscBundle with the given datagram.

        Args:
            dgram: a UDP datagram representing an OscBundle.

        Raises:
            ParseError: if the datagram could not be parsed into an OscBundle.
        """
        # Interesting stuff starts after the initial b"#bundle\x00".
        self._dgram = dgram
        index = len(_BUNDLE_PREFIX)
        try:
            self._timestamp, index = get_date(self._dgram, index)
        except ParseError as pe:
            raise ParseError(
                "Could not get the date from the datagram: %s" % pe)
        # Get the contents as a list of OscBundle and OscMessage.
        self._contents = self._parse_contents(index)

    def _parse_contents(self, index):
        contents = []

        try:
            # An OSC Bundle Element consists of its size and its contents.
            # The size is an int32 representing the number of 8-bit bytes in
            # the contents, and will always be a multiple of 4. The contents
            # are either an OSC Message or an OSC Bundle.
            while self._dgram[index:]:
                # Get the sub content size.
                content_size, index = get_int(self._dgram, index)
                # Get the datagram for the sub content.
                content_dgram = self._dgram[index:index + content_size]
                # Increment our position index up to the next possible content.
                index += content_size
                # Parse the content into an OSC message or bundle.
                if OscBundle.dgram_is_bundle(content_dgram):
                    contents.append(OscBundle(content_dgram))
                else:
                    contents.append(OscMessage(content_dgram))
        except (ParseError, IndexError) as e:
            raise ParseError("Could not parse a content datagram: %s" % e)

        return contents

    def content(self, index):
        """Returns the bundle's content 0-indexed."""
        return self._contents[index]

    def __iter__(self):
        """Returns an iterator over the bundle's content."""
        return iter(self._contents)

    @staticmethod
    def dgram_is_bundle(dgram):
        """Returns whether this datagram starts like an OSC bundle."""
        return dgram.startswith(_BUNDLE_PREFIX)
