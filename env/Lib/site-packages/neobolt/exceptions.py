#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Copyright (c) 2002-2019 "Neo4j,"
# Neo4j Sweden AB [http://neo4j.com]
#
# This file is part of Neo4j.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
This module contains the core driver exceptions.
"""

# RoutingError:
# - RoutingUnavailable (procedure not found)
# - RoutingBroken (unexpected response)
# - No routers available
#
# ConnectionError:
# - ConnectionUnavailable: Can't connect
# - Connection???: Connected but wrong protocol
# - ConnectionExpired: Connection died while in use
# - ConnectionPoolClosed: Connection pool closed
# - ConnectionTimedOut: Timed out while connecting
#
# AddressError:
# - Failed to resolve address
#
# CypherError:
# -
#
# ProtocolError:
# -


class ProtocolError(Exception):
    """ Raised when an unexpected or unsupported protocol event occurs.
    """


class ServiceUnavailable(Exception):
    """ Raised when no database service is available.
    """


class IncompleteCommitError(Exception):
    """ Raised when a disconnection occurs while still waiting for a commit
    response. For non-idempotent write transactions, this leaves the data
    in an unknown state with regard to whether the transaction completed
    successfully or not.
    """


class ConnectionExpired(Exception):
    """ Raised when a connection is no longer available for the
    purpose it was originally acquired.
    """


class SecurityError(Exception):
    """ Raised when an action is denied due to security settings.
    """


class CypherError(Exception):
    """ Raised when the Cypher engine returns an error to the client.
    """

    message = None
    code = None
    classification = None
    category = None
    title = None
    metadata = None

    @classmethod
    def hydrate(cls, message=None, code=None, **metadata):
        message = message or "An unknown error occurred."
        code = code or "Neo.DatabaseError.General.UnknownError"
        try:
            _, classification, category, title = code.split(".")
        except ValueError:
            classification = "DatabaseError"
            category = "General"
            title = "UnknownError"

        error_class = cls._extract_error_class(classification, code)

        inst = error_class(message)
        inst.message = message
        inst.code = code
        inst.classification = classification
        inst.category = category
        inst.title = title
        inst.metadata = metadata
        return inst

    @classmethod
    def _extract_error_class(cls, classification, code):
        if classification == "ClientError":
            try:
                return client_errors[code]
            except KeyError:
                return ClientError

        elif classification == "TransientError":
            try:
                return transient_errors[code]
            except KeyError:
                return TransientError

        elif classification == "DatabaseError":
            return DatabaseError

        else:
            return cls


class ClientError(CypherError):
    """ The Client sent a bad request - changing the request might yield a successful outcome.
    """


class DatabaseError(CypherError):
    """ The database failed to service the request.
    """


class TransientError(CypherError):
    """ The database cannot service the request right now, retrying later might yield a successful outcome.
    """


class DatabaseUnavailableError(TransientError):
    """
    """


class ConstraintError(ClientError):
    """
    """


class CypherSyntaxError(ClientError):
    """
    """


class CypherTypeError(ClientError):
    """
    """


class NotALeaderError(ClientError):
    """
    """


class Forbidden(ClientError, SecurityError):
    """
    """


class ForbiddenOnReadOnlyDatabaseError(Forbidden):
    """
    """


class AuthError(ClientError, SecurityError):
    """ Raised when authentication failure occurs.
    """


client_errors = {

    # ConstraintError
    "Neo.ClientError.Schema.ConstraintValidationFailed": ConstraintError,
    "Neo.ClientError.Schema.ConstraintViolation": ConstraintError,
    "Neo.ClientError.Statement.ConstraintVerificationFailed": ConstraintError,
    "Neo.ClientError.Statement.ConstraintViolation": ConstraintError,

    # CypherSyntaxError
    "Neo.ClientError.Statement.InvalidSyntax": CypherSyntaxError,
    "Neo.ClientError.Statement.SyntaxError": CypherSyntaxError,

    # CypherTypeError
    "Neo.ClientError.Procedure.TypeError": CypherTypeError,
    "Neo.ClientError.Statement.InvalidType": CypherTypeError,
    "Neo.ClientError.Statement.TypeError": CypherTypeError,

    # Forbidden
    "Neo.ClientError.General.ForbiddenOnReadOnlyDatabase": ForbiddenOnReadOnlyDatabaseError,
    "Neo.ClientError.General.ReadOnly": Forbidden,
    "Neo.ClientError.Schema.ForbiddenOnConstraintIndex": Forbidden,
    "Neo.ClientError.Schema.IndexBelongsToConstraint": Forbidden,
    "Neo.ClientError.Security.Forbidden": Forbidden,
    "Neo.ClientError.Transaction.ForbiddenDueToTransactionType": Forbidden,

    # AuthError
    "Neo.ClientError.Security.AuthorizationFailed": AuthError,
    "Neo.ClientError.Security.Unauthorized": AuthError,

    # NotALeaderError
    "Neo.ClientError.Cluster.NotALeader": NotALeaderError
}

transient_errors = {

    # DatabaseUnavailableError
    "Neo.TransientError.General.DatabaseUnavailable": DatabaseUnavailableError
}
