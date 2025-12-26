import asyncio

from fastapi import FastAPI


def test_app_imports():
    from app.main import App

    assert isinstance(App, FastAPI)
    assert App.title == "Portion Note API"


def test_lifespan_runs(monkeypatch):
    import app.main as main

    called = {"migrations": 0, "seed": 0, "close": 0}

    def FakeRunMigrations() -> None:
        called["migrations"] += 1

    def FakeSeedDatabase() -> None:
        called["seed"] += 1

    class DummyConnection:
        def close(self) -> None:
            called["close"] += 1

    def FakeGetConnection() -> DummyConnection:
        return DummyConnection()

    monkeypatch.setattr(main, "RunMigrations", FakeRunMigrations)
    monkeypatch.setattr(main, "SeedDatabase", FakeSeedDatabase)
    monkeypatch.setattr(main, "GetConnection", FakeGetConnection)

    async def RunLifespan() -> None:
        async with main.Lifespan(main.App):
            if hasattr(main, "Root"):
                payload = await main.Root()
                assert payload["name"] == "Portion Note API"

    asyncio.run(RunLifespan())

    assert called == {"migrations": 1, "seed": 1, "close": 1}
