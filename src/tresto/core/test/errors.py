class BaseTestExtractionError(Exception):
    pass


class TestExtractionFormatError(BaseTestExtractionError):
    pass


class TestExtractionSignatureError(BaseTestExtractionError):
    pass


class TestExtractionNoTestFunctionsError(BaseTestExtractionError):
    pass
