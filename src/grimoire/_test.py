from types import SimpleNamespace

_test = SimpleNamespace(
    type=SimpleNamespace,
    name="alice",
    score=97.5,
    active=True,
    tags=["admin", "beta"],
    counts=(3, 7, 12),
    meta={"region": "us-west", "tier": 2},
    profile=SimpleNamespace(
        age=30,
        emails=["alice@work.com", "alice@home.net"],
        prefs=SimpleNamespace(
            theme="dark",
            font_size=14,
            pinned_items=frozenset({101, 202}),
        ),
    ),
    history=[
        SimpleNamespace(action="login", ts=1700000000),
        SimpleNamespace(action="upload", ts=1700003600, details={"size_kb": 480}),
    ],
    dimensions=range(5),
    nothing=None,
)
