"""
Common regexps

Attributes:
    UUID4_REGEXP_STR: uuid4 str
    UUID4_REGEXP: compiled regexp  for request id string
    REQUEST_ID_REGEXP: compiled regexp  for request id string
"""
import re


UUID4_REGEXP_STR = '[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}'
UUID4_REGEXP = re.compile('^{}\Z'.format(UUID4_REGEXP_STR), re.I)
REQUEST_ID_REGEXP = re.compile('^[0-9]{10},[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}\Z', re.I)