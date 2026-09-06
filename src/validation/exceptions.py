class ValidationPipelineError(Exception):
    pass
class ReaderError(ValidationPipelineError):
    pass
class SourceNotFoundError(ReaderError):
    pass
class RecordValidationError(ValidationPipelineError):
    pass