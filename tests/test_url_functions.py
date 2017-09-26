import pytest

from sitecartographer.sitecartographer import (
    normalize_protocol,
    remove_fragment
)

# remove_fragment
def test_remove_fragment_full_url():
    assert (
        remove_fragment('https://foo.com/bar.html#baz') ==
        'https://foo.com/bar.html'
    )


def test_remove_fragment_fragment_only():
    assert remove_fragment('#baz') == ''


def test_remove_fragment_no_fragment():
    assert (
        remove_fragment('https://foo.com/bar.html') ==
        'https://foo.com/bar.html'
    )


# normalize_protocol
def test_normalize_protocol_http_to_https():
    assert normalize_protocol('http://foo.com', 'https') == 'https://foo.com'


def test_normalize_protocol_https_to_http():
    assert normalize_protocol('https://foo.com', 'http') == 'http://foo.com'


def test_normalize_protocol_http_to_http():
    assert normalize_protocol('http://foo.com', 'http') == 'http://foo.com'


def test_normalize_protocol_https_to_https():
    assert normalize_protocol('https://foo.com', 'https') == 'https://foo.com'


def test_normalize_protocol_http_scheme_relative_url():
    assert normalize_protocol('//foo.com', 'http') == 'http://foo.com'


def test_normalize_protocol_https_scheme_relative_url():
    assert normalize_protocol('//foo.com', 'https') == 'https://foo.com'


def test_normalize_protocol_invalid_protocol_arg():
    with pytest.raises(ValueError):
        normalize_protocol('https://foo.com', 'ftp')


def test_normalize_protocol_no_protocol_in_url():
    with pytest.raises(ValueError):
        normalize_protocol('foo.com', 'http')


def test_normalize_protocol_invalid_protocol_in_url():
    with pytest.raises(ValueError):
        normalize_protocol('ftp://foo.com', 'http')
