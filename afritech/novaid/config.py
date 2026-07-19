from dataclasses import dataclass
import os


@dataclass(frozen=True)
class NovaIDAuthenticationConfig:
    access_token_seconds: int = 900
    refresh_token_seconds: int = 604800
    refresh_family_seconds: int = 2592000
    otp_seconds: int = 300
    otp_maximum_attempts: int = 5
    session_idle_seconds: int = 1800
    session_absolute_seconds: int = 43200
    jwt_issuer: str = ""
    jwt_audience: str = ""
    jwt_algorithms: tuple[str, ...] = ("HS256",)

    @classmethod
    def from_environment(cls, environment: str | None = None) -> "NovaIDAuthenticationConfig":
        stage = (environment or os.getenv("AFRITECH_ENV", "development")).lower()
        config = cls(
            jwt_issuer=os.getenv("NOVAID_JWT_ISSUER", ""),
            jwt_audience=os.getenv("NOVAID_JWT_AUDIENCE", ""),
        )
        if stage in {"production", "prod"} and (not config.jwt_issuer or not config.jwt_audience):
            raise ValueError("missing_production_novaid_token_configuration")
        return config
