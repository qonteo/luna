import six
import json

from graphql.error import GraphQLError


def format_graphql_error(error):
    error = str(error)
    try:
        error = json.loads(error)
    except (json.JSONDecodeError, Exception):
        pass

    formatted_error = {
        'message': error,
    }

    if isinstance(error, GraphQLError):
        if error.locations is not None:
            formatted_error['locations'] = [
                {'line': loc.line, 'column': loc.column}
                for loc in error.locations
            ]

    return formatted_error


def format_luna_graphql_error(error):
    if isinstance(error, GraphQLError):
        return format_graphql_error(error)

    return {'message': six.text_type(error)}
