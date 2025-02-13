import json
from langchain_openai import ChatOpenAI
from .model import Agent, Response, json_to_markdown_table
import httpx

class TriageAgent(Agent):
    name: str = "Triage Agent"
    instructions: str = """
        You are the triage or orchestrator Agent for system issue troubleshooting. Your role is to handle initial user interaction, ask the user to provide supporting information such as logs, error messages, or any other relevant information. Do not perform any analysis or propose any solution.

        Always respond in English. However, if the user query is in Indonesian, reply in Indonesian consistently throughout the conversation.
        Do not hallucinate and only use the facts provided in the context.
        If the query is not related to system troubleshooting, respond politely that you are unable to help.

        Extract the following information from the provided input.
            'service_name' (str): this is in the k8s_container_name parameter in the log. If the log is not provided, identify based on exact service name in the input.
            'transaction_id' (str): this is in the ExceptionInfo.transactionId or "transaction_id" in the log
            'timestamp' (str): this is in the ExceptionInfo.timeStamp in the log

        Output: Your response should be returned as a JSON object. If there is no information available, set all the values with empty string.
            'service_name' (str)
            'transaction_id' (str)
            'timestamp' (str)
    """

    def transfer_to_logchecker(self):
        from .logchecker import LogCheckerAgent
        agent = LogCheckerAgent()
        return agent

    def execute(self, query) -> Response:
        """
        Executes the triage agent's process by querying the LLM model and processing the response.
        :param query: The input query from the user (typically a log or issue description).
        :return: A Response object containing the LLM's response and the extracted information.
        """
        next_agent = self

        print("Current agent: " + next_agent.name)

        # Initialize the LLM model (this is where you bind and configure the OpenAI API)
        llm = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            async_client=httpx.AsyncClient(verify=False),
            http_client=httpx.Client(verify=False),
            temperature=self.temperature
        )

        llm = llm.bind(response_format={"type": "json_object"})
        # Instructions for triage agent, passed to LLM in query
        

        # Add system instructions to the query

        query = [
            ("system", self.instructions),
        ] + query

        # Get the LLM response
        response = llm.invoke(query)

        # Parse the response JSON
        response_json = json.loads(response.content)
        
        # Extract service_name, transaction_id, and timestamp
        service_name = response_json.get('service_name', '')
        transaction_id = response_json.get('transaction_id', '')
        timestamp = response_json.get('timestamp', '')
        
        response_msg = []
        # Prepare the response message to return
        if service_name or transaction_id:
            response_msg = [{
                "role": "assistant",
                "content": "Thank you for the information. Here is what I understand: \n" + json_to_markdown_table(response.content, 1)
            }]
        
        if service_name and not transaction_id:
            response_msg.append({
                "role": "assistant",
                "content": "Please provide sample transaction id and all related logs for me to investigate the issue with: " + service_name
            })

            next_agent = self.transfer_to_logchecker()

        if (not service_name) and (not transaction_id):
            response_msg.append({
                "role": "assistant", 
                "content": "I'm sorry, in order for me to investigate, please provide the exact service name or sample transaction id."
            })

        if transaction_id:
            response_msg.append({
                "role": "assistant",
                "content": "Please provide logs for all related services for this transaction id: " + transaction_id
            })

            next_agent = self.transfer_to_logchecker()

        
        print("Current agent: " + next_agent.name)
        
        # Return the Response object with the extracted information
        return Response(
            agent=next_agent,
            messages=response_msg
        )
