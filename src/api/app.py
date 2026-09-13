"""FastAPI composition root for synchronous analysis and immutable retrieval."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Header, Request
from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.contracts import ApiError, ApiFieldError, ErrorResponse, HealthResponse
from src.core.config import Settings, get_settings
from src.core.errors import (
    ApplicationError,
    PersistenceError,
    RequestValidationError,
    ResultNotFoundError,
)
from src.mcp.client import FinanceMCPClient
from src.observability import (
    Observability,
    PersistenceTelemetryObserver,
    ToolTelemetryObserver,
    configure_structured_logging,
)
from src.orchestration.graph import AnalysisOrchestrator
from src.persistence.repository import FileResultRepository
from src.schemas.request import AnalysisRequest
from src.schemas.run import RunState
from src.services.analysis import AnalysisService
from src.services.metrics import MetricsSnapshot


def create_app(
    *,
    settings: Settings | None = None,
    service: AnalysisService | None = None,
) -> FastAPI:
    """Build an injectable app without making network calls or writing files."""

    effective_settings = settings or get_settings()
    configure_structured_logging(effective_settings.log_level)
    effective_service = service or _build_service(effective_settings)
    app = FastAPI(
        title=effective_settings.app_name,
        version="1.0.0",
        description="Typed, synchronous financial-analysis API backed by immutable JSON artifacts.",
    )
    app.state.analysis_service = effective_service
    app.state.settings = effective_settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=effective_settings.cors_allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Idempotency-Key"],
    )
    _register_exception_handlers(app)
    _register_routes(app)
    return app


def _build_service(settings: Settings) -> AnalysisService:
    observability = Observability()
    orchestrator = AnalysisOrchestrator(
        mcp_client=FinanceMCPClient(settings, observer=ToolTelemetryObserver(observability)),
        observability=observability,
    )
    return AnalysisService(
        runner=orchestrator,
        repository=FileResultRepository(
            settings.result_output_dir,
            observer=PersistenceTelemetryObserver(observability),
        ),
        observability=observability,
    )


def _get_service(request: Request) -> AnalysisService:
    return request.app.state.analysis_service  # type: ignore[no-any-return]


ServiceDependency = Annotated[AnalysisService, Depends(_get_service)]
IdempotencyHeader = Annotated[
    str | None,
    Header(alias="Idempotency-Key", min_length=1, max_length=120),
]


def _register_routes(app: FastAPI) -> None:
    @app.post(
        "/api/v1/analyses",
        response_model=RunState,
        responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
        summary="Execute and persist one analysis",
    )
    async def create_analysis(
        analysis_request: AnalysisRequest,
        service: ServiceDependency,
        idempotency_key: IdempotencyHeader = None,
    ) -> RunState:
        request_with_key = _apply_idempotency_key(analysis_request, idempotency_key)
        return await service.execute(request_with_key)

    @app.get(
        "/api/v1/analyses/{run_id}",
        response_model=RunState,
        responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
        summary="Load a persisted terminal analysis",
    )
    def get_analysis(run_id: UUID, service: ServiceDependency) -> RunState:
        return service.get(run_id)

    @app.get("/api/v1/health", response_model=HealthResponse, summary="Inspect process health")
    def health(request: Request) -> HealthResponse:
        settings: Settings = request.app.state.settings if hasattr(request.app.state, "settings") else get_settings()
        return HealthResponse(
            status="ok",
            app_name=settings.app_name,
            environment=settings.app_environment,
            storage="configured",
        )

    @app.get("/api/v1/metrics", response_model=MetricsSnapshot, summary="Read in-process metrics")
    def metrics(service: ServiceDependency) -> MetricsSnapshot:
        return service.metrics.snapshot()


def _apply_idempotency_key(
    analysis_request: AnalysisRequest, idempotency_key: str | None
) -> AnalysisRequest:
    body_key = analysis_request.idempotency_key
    if body_key is not None and idempotency_key is not None and body_key != idempotency_key:
        raise RequestValidationError(
            "The Idempotency-Key header must match the request idempotency_key.",
            operation="idempotency_validation",
            context={"field": "idempotency_key"},
        )
    if idempotency_key is None:
        return analysis_request
    return analysis_request.model_copy(update={"idempotency_key": idempotency_key})


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(FastAPIRequestValidationError)
    async def request_validation_handler(
        request: Request, exc: FastAPIRequestValidationError
    ) -> JSONResponse:
        _get_service(request).metrics.record_validation_failure()
        fields = [
            ApiFieldError(
                location=[str(item) if not isinstance(item, int) else item for item in error["loc"]],
                message=str(error["msg"]),
                type=str(error["type"]),
            )
            for error in exc.errors()
        ]
        return _error_response(
            status_code=422,
            code="request_validation_error",
            message="The request does not match the analysis contract.",
            fields=fields,
        )

    @app.exception_handler(ApplicationError)
    async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
        if isinstance(exc, PersistenceError):
            _get_service(request).metrics.record_persistence_failure()
        if isinstance(exc, RequestValidationError):
            _get_service(request).metrics.record_validation_failure()
        status_code = 404 if isinstance(exc, ResultNotFoundError) else 422 if isinstance(exc, RequestValidationError) else 500
        detail = exc.to_detail()
        fields = []
        if isinstance(exc, RequestValidationError):
            field = detail.context.get("field", "request")
            fields = [ApiFieldError(location=["body", str(field)], message=detail.message, type=detail.code)]
        return _error_response(
            status_code=status_code,
            code=detail.code,
            message=detail.message,
            context=detail.context,
            fields=fields,
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        del exc
        return _error_response(
            status_code=500,
            code="internal_error",
            message="The request could not be completed safely.",
        )


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    context: dict[str, object] | None = None,
    fields: list[ApiFieldError] | None = None,
) -> JSONResponse:
    payload = ErrorResponse(
        error=ApiError(code=code, message=message, context=context or {}, fields=fields or [])
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


app = create_app()
