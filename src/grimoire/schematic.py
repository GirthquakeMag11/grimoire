

class Schematic:
    name: str
    keys: list[str]
    primary_key: str
    required_keys: list[str]
    optional_keys: list[str]
    readonly_keys: list[str]
    total: bool
    defaults: dict[str, Any]
    default_factores: dict[str, Callable[[], Any]]
    annotations: dict[str, Any]
