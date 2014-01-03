from django.core.exceptions import ValidationError
from daffodil import Daffodil
from daffodil.exceptions import ParseError


def validate_daffodil_fltr(value):
    try:
        Daffodil(value)
    except ParseError, e:
        raise ValidationError("Invalid Daffodil filter. %s" % str(e))