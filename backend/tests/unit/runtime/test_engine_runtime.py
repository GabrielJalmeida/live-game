from app.runtime.engine import EngineRuntime


def test_engine_runtime_shares_realtime_manager():
    runtime = EngineRuntime()

    assert (
        runtime.experience_manager.realtime_manager
        is runtime.realtime_manager
    )