cube\utils\collections.py:10: note: PEP 484 prohibits implicit Optional. Accordingly, mypy has changed its default to no_implicit_optional=True
cube\utils\collections.py:10: note: Use https://github.com/hauntsaninja/no_implicit_optional to automatically upgrade your codebase

https://adamj.eu/tech/2022/10/18/python-type-hints-implicit-optional-types/
You can turn off by
[mypy]
implicit_optional = true

or
 see https://github.com/hauntsaninja/no_implicit_optional
 and fix some manually
