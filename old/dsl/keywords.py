from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel

class ActionType(str, Enum):
    """Types of actions that can be performed"""
    # Navigation actions
    GO_TO = "go to"
    OPEN = "open"
    REFRESH = "refresh"
    
    # Interaction actions
    CLICK = "click"
    ENTER = "enter"
    TYPE = "type"
    SELECT = "select"
    CHECK_ELEMENT = "check"
    UNCHECK = "uncheck"
    
    # Verification actions
    VERIFY = "verify"
    VALIDATE = "validate"
    ASSERT = "assert"
    
    # Wait actions
    WAIT_FOR = "wait for"
    WAIT_UNTIL = "wait until"
    WAIT_WHILE = "wait while"

class ElementType(str, Enum):
    """Types of elements that can be interacted with"""
    BUTTON = "button"
    LINK = "link"
    FIELD = "field"
    INPUT = "input"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    DROPDOWN = "dropdown"
    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    LIST = "list"
    DIV = "div"
    SPAN = "span"

class StateType(str, Enum):
    """Types of states that elements can be in"""
    # Visibility states
    VISIBLE = "visible"
    HIDDEN = "hidden"
    DISPLAYED = "displayed"
    
    # Interactivity states
    ENABLED = "enabled"
    DISABLED = "disabled"
    CLICKABLE = "clickable"
    
    # Selection states
    CHECKED = "checked"
    UNCHECKED = "unchecked"
    SELECTED = "selected"
    
    # Presence states
    PRESENT = "present"
    ABSENT = "absent"
    
    # Focus states
    FOCUSED = "focused"
    BLURRED = "blurred"
    
    # Content states
    EMPTY = "empty"
    NOT_EMPTY = "not empty"
    CONTAINS = "contains"
    
    # Value states
    HAS_VALUE = "has value"
    NO_VALUE = "no value"

class KeywordValidator:
    def __init__(self):
        self.actions = {action.value for action in ActionType}
        self.elements = {element.value for element in ElementType}
        self.states = {state.value for state in StateType}

    def validate_action(self, action: str) -> bool:
        """Validate if action is a valid keyword"""
        return action.lower() in self.actions

    def validate_element(self, element: str) -> bool:
        """Validate if element is a valid keyword"""
        return element.lower() in self.elements

    def validate_state(self, state: str) -> bool:
        """Validate if state is a valid keyword"""
        return state.lower() in self.states

    def validate_command(self, command: str) -> bool:
        """Validate if command contains valid keywords"""
        words = command.lower().split()
        return any(word in self.actions for word in words)

class KeywordExtractor:
    def __init__(self):
        self.validator = KeywordValidator()

    def extract_action(self, command: str) -> Optional[str]:
        """Extract action from command"""
        words = command.lower().split()
        for word in words:
            if self.validator.validate_action(word):
                return word
        return None

    def extract_element(self, command: str) -> Optional[str]:
        """Extract element from command"""
        words = command.lower().split()
        for word in words:
            if self.validator.validate_element(word):
                return word
        return None

    def extract_state(self, command: str) -> Optional[str]:
        """Extract state from command"""
        words = command.lower().split()
        for word in words:
            if self.validator.validate_state(word):
                return word
        return None

# Example usage
if __name__ == "__main__":
    validator = KeywordValidator()
    extractor = KeywordExtractor()

    # Test commands
    test_commands = [
        "click login button",
        "enter test@email.com into email field",
        "verify dashboard is visible",
        "wait for page to load",
        "check if error message is not visible"
    ]

    for command in test_commands:
        print(f"\nCommand: {command}")
        print(f"Valid command: {validator.validate_command(command)}")
        print(f"Action: {extractor.extract_action(command)}")
        print(f"Element: {extractor.extract_element(command)}")
        print(f"State: {extractor.extract_state(command)}") 