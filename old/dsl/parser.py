from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .keywords import KeywordValidator, KeywordExtractor, ActionType, ElementType, StateType

@dataclass
class ParsedCommand:
    """Represents a parsed command from natural language"""
    action: str
    element: Optional[str] = None
    value: Optional[str] = None
    state: Optional[str] = None
    attributes: Dict[str, str] = None
    negated: bool = False

class DSLParser:
    """Parser for converting natural language into structured commands"""
    
    def validate(self, command: str) -> bool:
        """
        Validate if a command can be parsed
        
        Args:
            command: Natural language command
            
        Returns:
            bool: True if command can be parsed
        """
        # Basic validation - check if command contains any known action
        command = command.lower()
        return any(action.value in command for action in ActionType)

    def parse(self, command: str) -> ParsedCommand:
        """
        Parse natural language command into structured format
        
        Args:
            command: Natural language command
            
        Returns:
            ParsedCommand: Structured command
        """
        command = command.lower()
        
        # Extract action
        action = self._extract_action(command)
        if not action:
            raise ValueError(f"No valid action found in command: {command}")
            
        # Extract element
        element = self._extract_element(command)
        
        # Extract value
        value = self._extract_value(command)
        
        # Extract state
        state = self._extract_state(command)
        
        # Extract attributes
        attributes = self._extract_attributes(command)
        
        # Check for negation
        negated = "not" in command or "isn't" in command or "isnt" in command
        
        return ParsedCommand(
            action=action,
            element=element,
            value=value,
            state=state,
            attributes=attributes,
            negated=negated
        )

    def _extract_action(self, command: str) -> Optional[str]:
        """Extract action from command"""
        for action in ActionType:
            if action.value in command:
                return action.value
        return None

    def _extract_element(self, command: str) -> Optional[str]:
        """Extract element from command"""
        words = command.split()
        for element_type in ElementType:
            if element_type.value in command:
                idx = words.index(element_type.value)
                if idx > 0:
                    return f"{words[idx-1]} {element_type.value}"
        return None

    def _extract_value(self, command: str) -> Optional[str]:
        """Extract value from command"""
        import re
        # Look for quoted values
        quoted = re.findall(r'"([^"]*)"', command) or re.findall(r"'([^']*)'", command)
        if quoted:
            return quoted[0]
            
        # Look for values after specific words
        words = command.split()
        for marker in ["with", "as", "to"]:
            if marker in words:
                idx = words.index(marker)
                if idx + 1 < len(words):
                    return words[idx + 1]
        return None

    def _extract_state(self, command: str) -> Optional[str]:
        """Extract state from command"""
        for state in StateType:
            if state.value in command:
                return state.value
        return None

    def _extract_attributes(self, command: str) -> Dict[str, str]:
        """Extract attributes from command"""
        attributes = {}
        # Look for key-value pairs in format: key=value or key:"value"
        import re
        # Match both quoted and unquoted attributes
        attr_patterns = [
            r'(\w+)="([^"]*)"',  # key="value"
            r"(\w+)='([^']*)'",  # key='value'
            r'(\w+)=(\w+)',      # key=value
        ]
        
        for pattern in attr_patterns:
            matches = re.findall(pattern, command)
            for key, value in matches:
                attributes[key.lower()] = value
                
        return attributes

# Example usage
if __name__ == "__main__":
    parser = DSLParser()
    
    # Test commands
    test_commands = [
        "click login button",
        "enter 'test@email.com' into email field",
        "verify dashboard is visible",
        "wait for page to load",
        "check if error message is not visible",
        "slowly drag the image to the upload area",
        "quickly double click the notification with id=alert",
        "repeatedly press the refresh button until page loads"
    ]
    
    for command in test_commands:
        print(f"\nCommand: {command}")
        if parser.validate(command):
            parsed = parser.parse(command)
            print(f"Parsed: {parsed}")
        else:
            print("Invalid command") 