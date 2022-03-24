from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport


def run_query(query):
    """Run a GraphQL query against the rata.digitraffic.fi server."""
    # Select your transport with a defined url endpoint
    transport = RequestsHTTPTransport(
        url="https://rata.digitraffic.fi/api/v2/graphql/graphql"
    )

    # Create a GraphQL client using the defined transport
    client = Client(transport=transport, fetch_schema_from_transport=True)

    # Execute the GraphQL query on the transport
    result = client.execute(gql(query))

    return result
