"""
User Interfaces and API Development Module

This module provides comprehensive user interfaces for the DDoS testing framework:
- Advanced command-line interface with intelligent auto-completion
- Modern web-based GUI with real-time updates
- REST and GraphQL APIs for programmatic access
- Mobile app support and remote management capabilities
"""

# Import CLI components (always available)
try:
    from .cli import AdvancedCLI, InteractiveMode, ScriptingEngine
except ImportError:
    AdvancedCLI = None
    InteractiveMode = None
    ScriptingEngine = None

# Import Web GUI components (may require additional dependencies)
try:
    from .web_gui import WebGUI, DashboardManager, VisualizationEngine
except ImportError:
    WebGUI = None
    DashboardManager = None
    VisualizationEngine = None

# Import API components (requires Flask and related packages)
try:
    from .api import RESTAPIServer, GraphQLAPIServer, WebSocketManager
except ImportError:
    RESTAPIServer = None
    GraphQLAPIServer = None
    WebSocketManager = None

# Import Mobile components (may require additional dependencies)
try:
    from .mobile import MobileAPIGateway, RemoteManagementService
except ImportError:
    MobileAPIGateway = None
    RemoteManagementService = None

__all__ = [
    'AdvancedCLI',
    'InteractiveMode', 
    'ScriptingEngine',
    'WebGUI',
    'DashboardManager',
    'VisualizationEngine',
    'RESTAPIServer',
    'GraphQLAPIServer',
    'WebSocketManager',
    'MobileAPIGateway',
    'RemoteManagementService'
]

__version__ = "1.0.0"