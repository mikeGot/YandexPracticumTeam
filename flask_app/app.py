import os
import re
from datetime import timedelta
from http import HTTPStatus

import constants
import jaeger
import messages
import redis
import requests
import sentry_sdk
from black_list import jwt_redis_blocklist
from config import settings
from db_models import User
from documentation import spec
from errors import ERROR_BASE_CODE, SERVER_ERROR
from flask import Flask, request
from flask_jwt_extended import JWTManager, get_jwt_identity, jwt_required
from flask_opentracing import FlaskTracer
from helpers import check_path
from limiter import limiter
from loguru import logger
from messages import ResponseForm
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from sentry_sdk.integrations.flask import FlaskIntegration
from services import user_role_service, user_service
from spectree import Response
from v1.auth.auth import auth_blueprint
from v1.auth.oauth import oauth_blueprint
from v1.roles.roles import roles_blueprint
from werkzeug.exceptions import HTTPException


sentry_sdk.init(
    dsn=settings.sentry_url,
    integrations=[
        FlaskIntegration(),
    ],
    traces_sample_rate=settings.sentry_traces_sample_rate
)


def configure_tracer() -> None:
    trace.set_tracer_provider(TracerProvider())
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(ConsoleSpanExporter())
    )


configure_tracer()

app = Flask(__name__)

FlaskInstrumentor().instrument_app(app)

app.register_blueprint(roles_blueprint, url_prefix=f"{settings.base_api_url}")
app.register_blueprint(auth_blueprint, url_prefix=f"{settings.base_api_url}")
app.register_blueprint(oauth_blueprint, url_prefix=f"{settings.base_api_url}")

spec.register(app)

limiter.init_app(app)

SECRET_KEY = os.urandom(32)
app.config["SECRET_KEY"] = SECRET_KEY

app.config["JWT_SECRET_KEY"] = settings.jwt_secret_key
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
    hours=settings.access_token_expires_in_hours
)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(
    days=settings.refresh_token_expires_in_days
)
app.config["TEMPLATES_AUTO_RELOAD"] = True

jwt = JWTManager(app)

jaeger.tracer = FlaskTracer(jaeger.setup_jaeger, app=app)


@app.before_request
def before_request():
    request_id = request.headers.get("X-Request-Id")
    if not request_id:
        logger.info("request id is required")


@app.errorhandler(Exception)
def handle_exception(e):

    if isinstance(e, HTTPException):
        return {
            "code": ERROR_BASE_CODE,
            "msg": re.sub(
                pattern=re.compile("<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});"),
                repl="",
                string=e.get_description(),
            ),
        }, e.code

    elif isinstance(e, Exception):
        if not settings.debug_mode_handler:
            return SERVER_ERROR, HTTPStatus.INTERNAL_SERVER_ERROR

        else:
            return {
                "code": ERROR_BASE_CODE,
                "msg": str(e),
            }, HTTPStatus.INTERNAL_SERVER_ERROR


@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload: dict):
    jti = jwt_payload["jti"]
    token_in_redis = True
    try:
        token_in_redis = jwt_redis_blocklist.get(jti)
    except redis.exceptions.ConnectionError:
        logger.error("Redis is not available!")

    return token_in_redis is not None


app.app_context().push()


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
@limiter.limit("10/minute")
@spec.validate(
    resp=Response(
        HTTP_200=ResponseForm,
        HTTP_401=ResponseForm,
        HTTP_403=ResponseForm,
        HTTP_500=ResponseForm,
    ),
    tags=["Gateway to movie service"],
)
@jwt_required(optional=True)
def catch_all(path):
    current_user = get_jwt_identity()

    if not current_user:
        result = {"permissions": constants.ROLE_UNAUTHORIZED_USER.permissions}
    else:
        user: User = user_service.get({"email": current_user})

        if not user:
            return ResponseForm(msg=messages.bad_token), HTTPStatus.UNAUTHORIZED

        result = user_role_service.get_permissions_of(current_user)

    if check_path(result["permissions"], path):
        url = f"http://{settings.backend_host}:{settings.backend_port}/" + path
        req = requests.models.PreparedRequest()
        req.prepare_url(url, request.args.to_dict())
        return ResponseForm(
            msg=messages.successful_response, result=requests.get(req.url).json()
        )
    else:
        return ResponseForm(msg=messages.not_allowed_resource), HTTPStatus.FORBIDDEN


if __name__ == "__main__":
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.run(host=settings.auth_server_host, port=settings.auth_server_port, debug=True)
