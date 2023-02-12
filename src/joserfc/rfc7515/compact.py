import binascii
from typing import Union, Optional, Any
from .types import ProtectedHeader
from .alg import JWSAlgorithm
from ..errors import DecodeError, MissingAlgorithmError
from .._util import (
    json_b64encode,
    json_b64decode,
    urlsafe_b64encode,
    urlsafe_b64decode,
)


class CompactData:
    def __init__(self, header: ProtectedHeader, payload: bytes,
                 signature: Optional[bytes]=None):
        self.header = header
        self.payload = payload
        self.signature = signature
        self._signing_input = None

    @property
    def signing_input(self) -> bytes:
        if self._signing_input:
            return self._signing_input

        protected_segment = json_b64encode(self.header)
        payload_segment = urlsafe_b64encode(self.payload)
        self._signing_input = protected_segment + b'.' + payload_segment
        return self._signing_input

    def sign(self, algorithm: JWSAlgorithm, key) -> bytes:
        self.signature = urlsafe_b64encode(algorithm.sign(self.signing_input, key))
        return self.signing_input + b'.' + self.signature

    def verify(self, algorithm: JWSAlgorithm, key) -> bool:
        sig = urlsafe_b64decode(self.signature)
        return algorithm.verify(self.signing_input, sig, key)


def serialize_compact(
    header: ProtectedHeader,
    payload: bytes,
    algorithm: JWSAlgorithm,
    key: Any) -> bytes:

    obj = CompactData(header, payload)
    return obj.sign(algorithm, key)


def extract_compact(text: bytes) -> CompactData:
    parts = text.split(b'.')
    if len(parts) != 3:
        raise ValueError('Invalid JSON Web Signature')

    header_segment, payload_segment, signature = parts
    try:
        header = json_b64decode(header_segment)
        if 'alg' not in header:
            raise MissingAlgorithmError()
    except (TypeError, ValueError, binascii.Error):
        raise DecodeError('Invalid header')

    try:
        payload = urlsafe_b64decode(payload_segment)
    except (TypeError, ValueError, binascii.Error):
        raise DecodeError('Invalid payload')

    obj = CompactData(header, payload, signature)
    obj._signing_input = header_segment + b'.' + payload_segment
    return obj