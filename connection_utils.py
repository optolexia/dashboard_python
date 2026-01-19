from dataclasses import dataclass
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
import os


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


@dataclass(frozen=True)
class ConnectionParameters:
    """
    Connection parameters object created based on environment variables
    """

    oplx_key_vault_uri = os.environ['oplx__keyvault__uri']
    research_key_vault_uri = os.environ['research__keyvault__uri']

    if 'local' in os.environ.keys():
        az_credential = InteractiveBrowserCredential(
            additionally_allowed_tenants=["1ee71642-f7d0-4b5b-8af1-051fb277e1b7"], logging_enable=True)
    else:
        az_credential = DefaultAzureCredential(additionally_allowed_tenants=["1ee71642-f7d0-4b5b-8af1-051fb277e1b7"],
                                               logging_enable=False)

    oplx_secret_client = SecretClient(vault_url=oplx_key_vault_uri, credential=az_credential, logging_enable=False)

    mysql_user = oplx_secret_client.get_secret("oplx-settlementreports-mysql-user", logging_enable=False).value
    mysql_pass = oplx_secret_client.get_secret("oplx-settlementreports-mysql-pass", logging_enable=False).value
    mysql_db = oplx_secret_client.get_secret("oplx-settlementreports-mysql-db", logging_enable=False).value
    mysql_port = int(oplx_secret_client.get_secret("oplx-settlementreports-mysql-port", logging_enable=False).value)
    mysql_host = oplx_secret_client.get_secret("oplx-settlementreports-mysql-host", logging_enable=False).value

    mysql_params = {"host": mysql_host, "port": mysql_port, "db": mysql_db, "user": mysql_user, "pass": mysql_pass}

    research_secret_client = SecretClient(vault_url=research_key_vault_uri, credential=az_credential,)

    pg_user = research_secret_client.get_secret("lexplore-analytics-pg-usr-admin", logging_enable=False).value
    pg_pass = research_secret_client.get_secret("lexplore-analytics-pg-pwd-admin", logging_enable=False).value
    pg_host = research_secret_client.get_secret("lexplore-analytics-pg-host", logging_enable=False).value
    pg_db = research_secret_client.get_secret("lexplore-analytcis-pg-db-dev", logging_enable=False).value
    #pg_port = int(oplx_secret_client.get_secret("lexplore-analytics-pg-db-dev", logging_enable=False).value)
    pg_params = {"host": pg_host, "db": pg_db, "user": pg_user, "pass": pg_pass}
