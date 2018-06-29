import datetime
import struct
import time

# Datagram length in bytes for types that have a fixed size.
_INT_DGRAM_LEN = 4
_FLOAT_DGRAM_LEN = 4
_DOUBLE_DGRAM_LEN = 8
_DATE_DGRAM_LEN = _INT_DGRAM_LEN * 2
# Strings and blob dgram length is always a multiple of 4 bytes.
_STRING_DGRAM_PAD = 4
_BLOB_DGRAM_PAD = 4

# conversion factor for fractional seconds (maximum value of fractional part)
FRACTIONAL_CONVERSION = 2 ** 32

# 63 zero bits followed by a one in the least signifigant bit is a special
# case meaning "immediately."
IMMEDIATELY = struct.pack('>q', 1)

# From NTP lib.
_SYSTEM_EPOCH = datetime.date(*time.gmtime(0)[0:3])
_NTP_EPOCH = datetime.date(1900, 1, 1)
# _NTP_DELTA is 2208988800
_NTP_DELTA = (_SYSTEM_EPOCH - _NTP_EPOCH).days * 24 * 3600


class NtpError(Exception):
    """Base class for ntp module errors."""


def ntp_to_system_time(date):
        """Convert a NTP time to system time.

        System time is reprensented by seconds since the epoch in UTC.
        """
        return date - _NTP_DELTA


def system_time_to_ntp(date):
        """Convert a system time to NTP time.

        System time is reprensented by seconds since the epoch in UTC.
        """
        try:
            num_secs = int(date)
        except ValueError as e:
            raise NtpError(e)

        num_secs_ntp = num_secs + _NTP_DELTA

        sec_frac = float(date - num_secs)

        picos = int(sec_frac * FRACTIONAL_CONVERSION)

        return struct.pack('>I', int(num_secs_ntp)) + struct.pack('>I', picos)


class ParseError(Exception):
    pass


def get_string(dgram, start_index):
    """Get a python string from the datagram, starting at pos start_index.

    According to the specifications, a string is:
    "A sequence of non-null ASCII characters followed by a null,
    followed by 0-3 additional null characters to make the total number
    of bits a multiple of 32".

    Args:
        dgram: A datagram packet.
        start_index: An index where the string starts in the datagram.

    Returns:
        A tuple containing the string and the new end index.

    Raises:
        ParseError if the datagram could not be parsed.
    """
    offset = 0
    try:
        while dgram[start_index + offset] != 0:
            offset += 1
        if offset == 0:
            raise ParseError('OSC string cannot begin with a null byte: %s' %
                             dgram[start_index:])
        # Align to a byte word.
        if (offset) % _STRING_DGRAM_PAD == 0:
            offset += _STRING_DGRAM_PAD
        else:
            offset += (-offset % _STRING_DGRAM_PAD)
        # Python slices do not raise an IndexError past the last index,
        # do it ourselves.
        if offset > len(dgram[start_index:]):
            raise ParseError('Datagram is too short')
        data_str = dgram[start_index:start_index + offset]
        return data_str.replace(b'\x00', b'').decode('utf-8'), \
            start_index + offset
    except IndexError as ie:
        raise ParseError('Could not parse datagram %s' % ie)
    except TypeError as te:
        raise ParseError('Could not parse datagram %s' % te)


def get_int(dgram, start_index):
    """Get a 32-bit big-endian two's complement integer from the datagram.

    Args:
        dgram: A datagram packet.
        start_index: An index where the integer starts in the datagram.

    Returns:
        A tuple containing the integer and the new end index.

    Raises:
        ParseError if the datagram could not be parsed.
    """
    try:
        if len(dgram[start_index:]) < _INT_DGRAM_LEN:
            raise ParseError('Datagram is too short')
        return (
            struct.unpack('>i',
                          dgram[start_index:start_index + _INT_DGRAM_LEN])[0],
            start_index + _INT_DGRAM_LEN)
    except (struct.error, TypeError) as e:
        raise ParseError('Could not parse datagram %s' % e)


def get_ttag(dgram, start_index):
    """Get a 64-bit OSC time tag from the datagram.

    Args:
        dgram: A datagram packet.
        start_index: An index where the osc time tag starts in the datagram.

    Returns:
        A tuple containing the tuple of time of sending in utc as datetime and
        the fraction of the current second and the new end index.

    Raises:
        ParseError if the datagram could not be parsed.
    """

    _TTAG_DGRAM_LEN = 8

    try:
        if len(dgram[start_index:]) < _TTAG_DGRAM_LEN:
            raise ParseError('Datagram is too short')

        seconds, idx = get_int(dgram, start_index)
        second_decimals, _ = get_int(dgram, idx)

        if seconds < 0:
            seconds += FRACTIONAL_CONVERSION

        if second_decimals < 0:
            second_decimals += FRACTIONAL_CONVERSION

        hours, seconds = seconds // 3600, seconds % 3600
        minutes, seconds = seconds // 60, seconds % 60

        utc = datetime.combine(_NTP_EPOCH, datetime.min.time()) + \
            datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)

        return (utc, second_decimals), start_index + _TTAG_DGRAM_LEN
    except (struct.error, TypeError) as e:
        raise ParseError('Could not parse datagram %s' % e)


def get_float(dgram, start_index):
    """Get a 32-bit big-endian IEEE 754 floating point number from the datagram.

    Args:
        dgram: A datagram packet.
        start_index: An index where the float starts in the datagram.

    Returns:
        A tuple containing the float and the new end index.

    Raises:
        ParseError if the datagram could not be parsed.
    """
    try:
        if len(dgram[start_index:]) < _FLOAT_DGRAM_LEN:
            # Noticed that Reaktor doesn't send the last bunch of \x00 needed
            # to make the float representation complete in some cases, thus we
            # pad here to account for that.
            dgram = dgram + \
                b'\x00' * (_FLOAT_DGRAM_LEN - len(dgram[start_index:]))
        return (
            struct.unpack('>f',
                          dgram[start_index:start_index +
                                _FLOAT_DGRAM_LEN])[0],
            start_index + _FLOAT_DGRAM_LEN)
    except (struct.error, TypeError) as e:
        raise ParseError('Could not parse datagram %s' % e)


def get_double(dgram, start_index):
    """Get a 64-bit big-endian IEEE 754 floating point number from the datagram.

    Args:
        dgram: A datagram packet.
        start_index: An index where the double starts in the datagram.

    Returns:
        A tuple containing the double and the new end index.

    Raises:
        ParseError if the datagram could not be parsed.
    """
    try:
        if len(dgram[start_index:]) < _DOUBLE_DGRAM_LEN:
            raise ParseError('Datagram is too short')
        return (struct.unpack('>d',
                              dgram[start_index:start_index +
                                    _DOUBLE_DGRAM_LEN])[0],
                start_index + _DOUBLE_DGRAM_LEN)
    except (struct.error, TypeError) as e:
        raise ParseError('Could not parse datagram {}'.format(e))


def get_blob(dgram, start_index):
    """ Get a blob from the datagram.

    According to the specifications, a blob is made of
    "an int32 size count, followed by that many 8-bit bytes of arbitrary
    binary data, followed by 0-3 additional zero bytes to make the total
    number of bits a multiple of 32".

    Args:
        dgram: A datagram packet.
        start_index: An index where the float starts in the datagram.

    Returns:
        A tuple containing the blob and the new end index.

    Raises:
        ParseError if the datagram could not be parsed.
    """
    size, int_offset = get_int(dgram, start_index)
    # Make the size a multiple of 32 bits.
    total_size = size + (-size % _BLOB_DGRAM_PAD)
    end_index = int_offset + size
    if end_index - start_index > len(dgram[start_index:]):
        raise ParseError('Datagram is too short.')
    return dgram[int_offset:int_offset + size], int_offset + total_size


def get_rgba(dgram, start_index):
    """Get an rgba32 integer from the datagram.

    Args:
        dgram: A datagram packet.
        start_index: An index where the integer starts in the datagram.

    Returns:
        A tuple containing the integer and the new end index.

    Raises:
        ParseError if the datagram could not be parsed.
    """
    try:
        if len(dgram[start_index:]) < _INT_DGRAM_LEN:
            raise ParseError('Datagram is too short')
        return (
            struct.unpack('>I',
                          dgram[start_index:start_index + _INT_DGRAM_LEN])[0],
            start_index + _INT_DGRAM_LEN)
    except (struct.error, TypeError) as e:
        raise ParseError('Could not parse datagram %s' % e)


def get_midi(dgram, start_index):
    """Get a MIDI message (port id, status byte, data1, data2) from the datagram.

    Args:
        dgram: A datagram packet.
        start_index: An index where the MIDI message starts in the datagram.

    Returns:
        A tuple containing the MIDI message and the new end index.

    Raises:
        ParseError if the datagram could not be parsed.
    """
    try:
        if len(dgram[start_index:]) < _INT_DGRAM_LEN:
            raise ParseError('Datagram is too short')
        val = struct.unpack('>I',
                            dgram[start_index:start_index + _INT_DGRAM_LEN])[0]
        midi_msg = tuple((val & 0xFF << 8 * i) >> 8 * i
                         for i in range(3, -1, -1))
        return (midi_msg, start_index + _INT_DGRAM_LEN)
    except (struct.error, TypeError) as e:
        raise ParseError('Could not parse datagram %s' % e)


def get_date(dgram, start_index):
    """Get a 64-bit big-endian fixed-point time tag as a date from the datagram.

    According to the specifications, a date is represented as is:
    "the first 32 bits specify the number of seconds since midnight on
    January 1, 1900, and the last 32 bits specify fractional parts of a second
    to a precision of about 200 picoseconds".

    Args:
        dgram: A datagram packet.
        start_index: An index where the date starts in the datagram.

    Returns:
        A tuple containing the system date and the new end index.
        returns osc_immediately (0) if the corresponding OSC sequence was
        found.

    Raises:
        ParseError if the datagram could not be parsed.
    """
    # Check for the special case first.
    if dgram[start_index:start_index + _DATE_DGRAM_LEN] == IMMEDIATELY:
        return IMMEDIATELY, start_index + _DATE_DGRAM_LEN
    if len(dgram[start_index:]) < _DATE_DGRAM_LEN:
        raise ParseError('Datagram is too short')
    num_secs, start_index = get_int(dgram, start_index)
    fraction, start_index = get_int(dgram, start_index)
    # Sum seconds and fraction of second:
    system_time = num_secs + (fraction / FRACTIONAL_CONVERSION)

    return ntp_to_system_time(system_time), start_index
