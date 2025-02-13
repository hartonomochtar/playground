# agents/agent.py
from pydantic import BaseModel
from typing import List, Optional
import json
import tiktoken

class Agent(BaseModel):
    name: str = "Agent"
    model: str = "deepseek-r1:8b"
    api_key: str = "EMPTY" 
    temperature: str = "0.0"
    instructions: str = "You are a helpful Agent"
    base_url: str = "http://localhost:11434/v1/"  # Default base URL

    # Define an execute method in the Agent class that subclasses can override
    def execute(self, input_data: str):
        raise NotImplementedError("The execute method must be implemented by the agent.")


class Response(BaseModel):
    agent: Optional[Agent]
    messages: list

import json

def json_to_markdown_table(json_data, mode=1):
    # Ensure the data is a dictionary (JSON parsed object)
    if isinstance(json_data, str):
        json_data = json.loads(json_data)

    markdown = ""

    if mode == 1:
        # Mode 1: Standard table layout
        # Add each key-value pair from the JSON
        markdown += "<table>"
        for key, value in json_data.items():
            markdown += f"<tr><td> <strong>{key}</strong> </td><td> {value} </td></tr>\n"
        markdown += "</table>"
    elif mode == 2:
        # Mode 2: Alternating layout (key, then value)

        first_item = True
        for key, value in json_data.items():
            if first_item:
                markdown += f"| **{key.title()}** |\n"
                markdown += "| ----- |\n"
                markdown += f"| {str(value)} |\n"
                first_item = False
            else:
                markdown += f"| **{key.title()}** |\n"
                markdown += f"| {str(value)} |\n"

    return markdown

def count_and_truncate_tokens(input_string, max_allowed_tokens):
    # Initialize the tiktoken tokenizer
    tokenizer = tiktoken.get_encoding("o200k_base")
    
    # Count the number of tokens in the input string
    tokens = tokenizer.encode(input_string)
    num_tokens = len(tokens)
    
    # Check if the token count exceeds the max allowed
    if num_tokens > max_allowed_tokens:
        # Truncate tokens to the max allowed limit
        truncated_tokens = tokens[:max_allowed_tokens]
        # Decode the truncated tokens back to a string
        truncated_string = tokenizer.decode(truncated_tokens)
        return truncated_string  # Return truncated string and original token count
    else:
        return input_string  # Return original string and token count if within limit
