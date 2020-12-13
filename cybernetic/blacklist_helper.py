from datetime import datetime
from flask_jwt_extended import decode_token
from cybernetic.Models import Token
from sqlalchemy.orm.exc import NoResultFound
from cybernetic import db


class TokenNotFound(Exception):
    """
    Indicates that a token could not be found in the database
    """
    pass


def _epoch_utc_to_datetime(epoch_utc):
    """
    Helper function for converting epoch timestamps (as stored in JWTs) into
    python datetime objects (which are easier to use with sqlalchemy).
    """
    return datetime.fromtimestamp(epoch_utc)


def add_token_to_database(encoded_token, identity_claim):
    """
    Adds a new token to the database. It is not revoked when it is added.
    :param encoded_token:
    :param identity_claim:
    """
    decoded_token = decode_token(encoded_token)
    jti = decoded_token['jti']
    token_type = decoded_token['type']
    user_identity = decoded_token[identity_claim]
    expires = _epoch_utc_to_datetime(decoded_token['exp'])
    revoked = False

    db_token = Token(
        jti=jti,
        token_type=token_type,
        user_identity=user_identity,
        expires=expires,
        revoked=revoked,
    )
    db.session.add(db_token)
    db.session.commit()


def is_token_revoked(decoded_token):
    """
    Checks if the given token is revoked or not. Because we are adding all the
    tokens that we create into this database, if the token is not present
    in the database we are going to consider it revoked, as we don't know where
    it was created.
    """
    jti = decoded_token['jti']
    try:
        token = Token.query.filter_by(jti=jti).one()
        return token.revoked
    except NoResultFound:
        return True


def get_user_tokens(user_identity):
    """
    Returns all of the tokens, revoked and unrevoked, that are stored for the
    given user
    """
    return Token.query.filter_by(user_identity=user_identity).all()


def revoke_token(token_jti, user):
    """
    Revokes the given token. Raises a TokenNotFound error if the token does
    not exist in the database
    """
    try:
        token = Token.query.filter_by(jti=token_jti, user_identity=user).one()
        token.revoked = True
        db.session.commit()
    except NoResultFound:
        raise TokenNotFound("Could not find the token {}".format(token_jti))


def revoke_tokens(user):
    """
    Revokes the given token. Raises a TokenNotFound error if the token does
    not exist in the database
    """
    tokens = Token.query.filter_by(user_identity=user).all()
    for token in tokens:
        token.revoked = True
        db.session.commit()



def unrevoke_token(token_id, user):
    """
    Unrevokes the given token. Raises a TokenNotFound error if the token does
    not exist in the database
    """
    try:
        token = Token.query.filter_by(id=token_id, user_identity=user).one()
        token.revoked = False
        db.session.commit()
    except NoResultFound:
        raise TokenNotFound("Could not find the token {}".format(token_id))


def prune_database():
    """
    Delete tokens that have expired from the database.
    How (and if) you call this is entirely up you. You could expose it to an
    endpoint that only administrators could call, you could run it as a cron,
    set it up with flask cli, etc.
    """
    now = datetime.now()
    expired = Token.query.filter(Token.expires < now).all()
    for token in expired:
        db.session.delete(token)
    db.session.commit()
