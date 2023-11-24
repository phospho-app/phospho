"""
Put some text here
"""
import contextvars
from typing import Union


class Agent:
    # Init method at the end of the class

    # Methods

    # ROUTES

    # Info route
    # Returns a dictionary with the agent's info
    # This method should not send sensitive information
    def get_info(self):
        response = {}

        response["name"] = self.name
        response["version"] = self.version
        response["params"] = self.params

        response["routes"] = []
        # Add the ask routes defined by the user
        for route in self.routes:
            response["routes"].append(route)

        return response

    # Ask route
    def ask(self, **ask_options):
        def decorator(callback):
            self.routes["ask"] = (callback, ask_options)
            return callback

        return decorator

    def handle_ask_request(
        self, *args, **kwargs
    ):  # TODO : have a rigid input format -> Message object
        # TODO: Validate the input format
        if "ask" in self.routes:  # Check if the route exists
            callback, ask_options = self.routes["ask"]

            # Check if the 'stream' parameter is set
            # TODO : webhook implementation here
            if "stream" in ask_options:
                stream_value = ask_options["stream"]
                if stream_value:
                    # TODO: implement the stream logic
                    return callback(*args, **kwargs)
                else:
                    return callback(*args, **kwargs)
            else:
                stream_value = False  # Set a default value if 'stream' is not provided
                return callback(*args, **kwargs)

        else:
            raise ValueError(f"Ask route not found.")

    # Chat route
    def chat(self, **ask_options):
        def decorator(callback):
            self.routes["chat"] = (callback, ask_options)
            return callback

        return decorator

    def handle_chat_request(
        self, *args, **kwargs
    ):  # TODO : have a rigid input format -> Message object
        # TODO: Validate the input format
        # TODO: handle Websockets and Streaming

        if "chat" in self.routes:  # Check if the route exists
            callback, ask_options = self.routes["chat"]

            # Check if the 'stream' parameter is set -> not in use know, but for reference on how to add options
            if "verbose" in ask_options:
                verbose_value = ask_options["verbose"]
                if verbose_value:
                    # TODO: implement the stream logic
                    print("Verbose = True")
                    return callback(*args, **kwargs)
                else:
                    return callback(*args, **kwargs)
            else:
                verbose_value = False  # Set a default value if 'stream' is not provided
                return callback(*args, **kwargs)

        else:
            raise ValueError(f"Chat route not found.")

    # SESSION
    # TODO: put it in a separate file
    class Session:
        def __init__(self, session_id: Union[str, None]):
            self.session_id = session_id

        def update_session_id(self, session_id):
            self.session_id = session_id

        # DEV
        def return_session_id(self):
            return self.session_id

    # Update the session id in the agent's subclass
    def update_session_id(self, session_id):
        # update the agent context attribute
        self.context["session_id"].set(session_id)

        # update the agent session sub-object
        self.session.update_session_id(self.context["session_id"].get())

    # Get the session id from the agent's subclass
    def get_session_id(self):
        return self.session.return_session_id()

    # Class level initialization
    def __init__(
        self,
        name="",
        version=None,  # optional version number of the agent
        params={},
    ):
        # Attributes
        self.name = name
        self.version = version
        self.params = params

        # Attribute for context variables
        context = {}
        # Attribute for session variable
        context["session_id"] = contextvars.ContextVar("session_id", default=None)
        self.context = context

        # Attributes for the routes handling
        self.routes = {}

        # Attributes for the session handling
        self.session = self.Session(
            self.context["session_id"]
        )  # has to be updated all the time
