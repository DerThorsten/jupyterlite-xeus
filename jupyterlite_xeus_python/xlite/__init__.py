from .xpython import XPythonBuilder
from .xsqlite import XSqliteBuilder
from .xlite import XLiteBuilderBase

# register
xlite_builders = {
    "python": XPythonBuilder,
    "sqlite": XSqliteBuilder,
}
def get_xlite_builder(name):
    return xlite_builders.get(name, XLiteBuilderBase)