from .xlite import XLiteBuilderBase

class XSqliteBuilder(XLiteBuilderBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)