from loguru import logger
from sqlalchemy.exc import IntegrityError

import constants
from services import role_service


def create_test_roles():
    try:
        role_service.insert(constants.ROLE_USER)
        role_service.insert(constants.ROLE_SUBSCRIBER)
        role_service.insert(constants.ROLE_ADMIN)
        role_service.insert(constants.ROLE_OWNER)
    except IntegrityError as e:
        logger.info("Roles have been already created")


create_test_roles()
