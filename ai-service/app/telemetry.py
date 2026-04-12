"""OpenTelemetry instrumentation for the AI service."""

import os

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

tracer = trace.get_tracer("grocery-ai")


def setup_telemetry(app):
    """Configure OpenTelemetry tracing."""
    resource = Resource.create({"service.name": "grocery-ai"})
    provider = TracerProvider(resource=resource)

    otel_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otel_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter(endpoint=otel_endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(exporter))
        except Exception as e:
            print(f"OTLP exporter setup failed: {e}")

    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
