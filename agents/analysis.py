import json
from langchain_openai import ChatOpenAI
from .model import Agent, Response, json_to_markdown_table
import httpx

class AnalysisAgent(Agent):
    name: str = "Analysis Agent"
    instructions: str = """
        You are an expert in system troubleshooting to identify the root causes of issues across multiple systems.

        The information related to order details, list of systems, workflow diagram, workflow description, and detailed system logs are provided below. Use all the available context, information, and facts to conduct a thorough analysis.

        Perform an in-depth analysis to identify all root causes and impacted systems.

        Make sure to consider all possible contributing factors and systems, and do not focus on a single cause without exploring others. Provide a clear connection between each identified issue and the systems impacted by it.

        Do not hallucinate and only use the facts provided in the context.

        Instructions for Output: Your response should be returned as a JSON object with the following keys. JSON must never be wrapped in code blocks (```). You must escape all JSON special characters accordingly.
        "score" (int): A score between 0 and 100, where 0 is the lowest and 100 is the highest, indicating the quality and accuracy of your root cause analysis.
        "rca" (string): A concise statement identifying the main root cause(s) based on your analysis.  Identify the following parameters when available.
        service name: this is in the service.hostname parameter in the log
        APIGW route: this is in the route.paths{} parameter in the log
        ESB container name: this is the k8s.container.name, if the value is "proxy" do not mention this parameter.
        "analysis" (string): A detailed explanation of the root cause(s), covering all contributing factors and impacted systems. Break down your reasoning step by step, explaining how each fact in the provided context led to your conclusion.
        Important Notes:

        Reasoning steps should precede your conclusion in the output.
        If there are multiple root causes, provide a detailed analysis of each.
        Avoid jumping to conclusions; follow a logical analysis based on the provided facts.
        Here are the order details, system information, workflow description, and logs for you to analyze:
        Double check the response format and make sure all JSON special characters are escaped properly.
    """

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

        print(query)
        # Get the LLM response
        response = llm.invoke(query)

        # Parse the response JSON
        response_json = json.loads(response.content)
        
        # Extract service_name, transaction_id, and timestamp
        score = response_json.get('score', '')
        rca = response_json.get('rca', '')
        analysis = response_json.get('analysis', '')

        print(response.content)

        # Prepare the response message to return
        response_msg = [{
            "role": "assistant",
            "content": json_to_markdown_table(response.content, 2)
        }]
        
        # Return the Response object with the extracted information
        return Response(
            agent=next_agent,
            messages=response_msg
        )
