"""Exercise the pinned OpenTelemetry SDK with in-memory export only."""
import json
from opentelemetry import trace
from opentelemetry.propagate import inject,extract
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import Status,StatusCode


def exercise(configured):
    exporter=InMemorySpanExporter()
    provider=TracerProvider() if configured else trace.NoOpTracerProvider()
    if configured:provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer=provider.get_tracer('learning-financial-order')
    carrier={}
    with tracer.start_as_current_span('gateway') as root:
        root.set_attribute('operation.id','ORDER-1');root.set_attribute('request.id','REQUEST-1')
        inject(carrier)
        with tracer.start_as_current_span('provider',context=extract(carrier)) as child:
            child.set_attribute('operation.id','ORDER-1');child.set_attribute('request.id','REQUEST-1')
            child.record_exception(RuntimeError('controlled provider failure'))
            child.set_status(Status(StatusCode.ERROR))
    spans=list(exporter.get_finished_spans());by_name={span.name:span for span in spans}
    result={'exported_spans':len(spans),'traceparent_propagated':'traceparent' in carrier}
    if configured:
        result.update(span_names=sorted(by_name),same_trace=by_name['gateway'].context.trace_id==by_name['provider'].context.trace_id,
            parent_matches=by_name['provider'].parent.span_id==by_name['gateway'].context.span_id,
            failed_spans=sum(span.status.status_code==StatusCode.ERROR for span in spans),
            request_ids=len({span.attributes['request.id'] for span in spans}))
        provider.shutdown()
    return result

if __name__=='__main__':
    print(json.dumps({'before':exercise(False),'after':exercise(True)},sort_keys=True))
