import ldclient
from ldclient.context import Context, ContextBuilder
from ldclient.config import Config
from typing import Union, Dict, Any
import dotenv
import uuid

dotenv.load_dotenv()

FlagValue = Union[bool, str, int, float, Dict[str, Any]]

class FeatureFlags:
    def __init__(self, sdk_key: str):
        self.ldclient = None
        try:
            self.ldclient = ldclient.get()
            if not self.ldclient.is_initialized():
                raise Exception("LaunchDarkly client not initialized")
        except:
            config = Config(sdk_key)
            ldclient.set_config(config)
            self.ldclient = ldclient.get()

    def get_flag(self, flag_key: str, default: FlagValue) -> FlagValue:
        return self.ldclient.variation(flag_key, Context(kind=Context.DEFAULT_KIND, key=str(uuid.uuid4()), anonymous=True), default)

    def get_user_flag(self, flag_key: str, user_id: str, default: FlagValue) -> FlagValue:
        """
        Get the value of a feature flag for a given context.

        Args:
            flag_key (str): The key of the feature flag.
            context (ldclient.Context): A LaunchDarkly Context object containing user information.
            default (FlagValue): The default value if the flag is not found.

        Returns:
            FlagValue: The value of the feature flag, which can be a boolean, string, number, or JSON object.
        """
        context = ContextBuilder("user").key(user_id).build()
        return self.ldclient.variation(flag_key, context, default)

    def close(self):
        """
        Close the LaunchDarkly client.
        """
        self.ldclient.close()