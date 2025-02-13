import json
from langchain_openai import ChatOpenAI
from .model import Agent, Response, count_and_truncate_tokens
import requests
import httpx

def query_log(search_term, index):
    url = 'https://splunk-query-accenture-poc-application.apps.cluster-gdm2g.gdm2g.sandbox1647.opentlc.com/search'
    headers = {
        'Content-Type': 'application/json',
        'Cookie': 'cd67134e12541f7d6958784e76a83787=32723587ad3d005624226c556d17f279'
    }
    data = {
        "search_term": search_term,
        "index": index
    }

    # Send POST request
    response = requests.post(url, headers=headers, data=json.dumps(data))

    # Check for successful response
    if response.status_code == 200:
        return response.json()["results"]  # or response.text depending on the format of the response
    else:
        return f"Error: {response.status_code}, {response.text}"


class LogRetrieverAgent(Agent):
    name: str = "Log Retriever Agent"
    instructions: str = """
        You are the Log Retriever Agent responsible for fetching log data from Splunk based on the provided service name.

        You must fetch log data from Splunk based on the service name provided by the user. Use the service name to query the log data and provide the relevant log details to the user.

        The log data must be fetched from Splunk based on the provided service name.
        The log data must be relevant to the service name provided.
        Once the log is available, transfer to Analysis Agent to perform the detailed root cause analysis.

    """

    def transfer_to_triage(self):
        from .triage import TriageAgent
        return TriageAgent()
    
    def transfer_to_analysis(self):
        from .analysis import AnalysisAgent
        return AnalysisAgent()

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
        
        
        # print(query)
        # # Get the LLM response
        # response = llm.invoke(logcheck_query)

        # # Parse the response JSON
        # response_json = json.loads(response.content)
        
        response_msg = []


        search_term = "DGPS241129073313898785093"
        index = "test_index_01"

        result = query_log(search_term, index)
        result_str = json.dumps(result)
        print(len(result_str))
        result_str = count_and_truncate_tokens(result_str, 70000)
        print(len(result_str))
        
        response_msg = [{
            "role": "user",
            "content": result_str
        }]

        next_agent = self.transfer_to_analysis()
        print(type(query))
        print(type(result))
        logretriever_query = query + response_msg

        response = next_agent.execute(logretriever_query)
        response_msg = response_msg + response.messages

        # Return the Response object with the extracted information
        return Response(
            agent=next_agent,
            messages=response_msg
        )
