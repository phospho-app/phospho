"""
Put some text here
"""
import contextvars

class Agent:
    # Constructor method (optional)
    def __init__(self, 
                name,
                version=None, # optional version number of the agent
                params = {}
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

    # Methods

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
    
    def handle_ask_request(self, *args, **kwargs): # TODO : have a rigid input format -> Message object
        if "ask" in self.routes: # Check if the route exists
            callback, ask_options = self.routes["ask"]

            # Check if the 'stream' parameter is set
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