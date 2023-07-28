"""
Put some text here
"""

class Agent:
    # Constructor method (optional)
    def __init__(self, 
                name,
                cpu=1,
                memory="16Gi",
                python_version="python3.8",
                python_packages="", # e.g. reuirements.txt or a list of packages names
                version=None, # optional version number of the agent
                params = {}
            ):

        # Attributes
        self.name = name
        self.cpu = cpu
        self.memory = memory
        self.python_version = python_version
        self.python_packages = python_packages
        self.version = version
        self.params = params

        # Attributes for the routes handling
        self.ask_routes = {}
        # self.chat_routes = {}
        # self.custom_routes = {}

    # Methods

    # Info route
    # Returns a dictionary with the agent's info
    def get_info(self):
        response = {}

        response["name"] = self.name
        response["version"] = self.version
        response["params"] = self.params

        response["routes"] = []
        for route in self.ask_routes:
            response["routes"].append(route)
        
        return response
        
    # Ask route
    def ask(self):
        id = "default"
        def decorator(callback):
            self.ask_routes[id] = callback
            return callback
        return decorator
    
    def handle_ask_request(self, id, *args, **kwargs):
        if id in self.ask_routes:
            callback = self.ask_routes[id]
            return callback(*args, **kwargs)
        else:
            raise ValueError(f"Ask route '{id}' not found.")