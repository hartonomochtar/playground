import json
from langchain_openai import ChatOpenAI
from .model import Agent, Response
import httpx

class LogCheckerAgent(Agent):
    name: str = "Log Checker Agent"
    instructions: str = """
        First analyze carefully the intent of the input: if it asks to search or says do not have or dont have or don't have any logs, set the search (bool) in the response to True. Otherwise set to False
        
        Your main task is to compare and check if the given log in the input has the key parameters.
        Evaluate how closely the input log aligns with the expected format structure.
        Provide a JSON response containing the following parameters:
            search (bool): if it asks to search or says do not have or dont have or don't have any logs, set to True. Else set to False.
            score (int): A numerical score between 0 and 100 representing how closely the input log aligns with the expected log structure (100 = perfect match, 0 = no match).
            reason (str): A brief comment explaining the analysis, outlining specific differences or similarities found in the log structure.

        Do not hallucinate and only use the facts provided in the context.

        Key parameters:
            "ExceptionInfo.apiID"
            "ExceptionInfo.channel"
            "ExceptionInfo.exceptionCategory"
            "ExceptionInfo.exceptionCode"
            "ExceptionInfo.exceptionMessage"
            "ExceptionInfo.httpStatusCode"
            "ExceptionInfo.processTime"
            "ExceptionInfo.serviceId"
            "ExceptionInfo.serviceIdB"
            "ExceptionInfo.timeStamp"
            "ExceptionInfo.traceId"
            "ExceptionInfo.transactionId"
            "FaultDetails.trace"
            "container.id"
            "container.image.name"
            "container.image.tag"
            "k8s.cluster.name"
            "k8s.container.name"
            "k8s.container.restart_count"
            "k8s.namespace.name"
            "k8s.node.name"
            "k8s.pod.labels.app"
            "k8s.pod.name"
            "k8s.pod.uid"
            "k8s_cluster_name"
            "k8s_container_name"
            "k8s_container_restart_count"
            "k8s_namespace_name"
            "k8s_node_name"
            "k8s_pod_labels_app"
            "k8s_pod_name"
            "k8s_pod_uid"

        Input Log:

    """

    def transfer_to_triage(self):
        from .triage import TriageAgent
        return TriageAgent()
    
    def transfer_to_analysis(self):
        from .analysis import AnalysisAgent
        return AnalysisAgent()
    
    def transfer_to_log_retriever(self):
        from .logretriever import LogRetrieverAgent
        return LogRetrieverAgent()

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
        
        logcheck_query = [
            ("system", self.instructions + query[-1]['content']),
        ]

        print(query)
        # Get the LLM response
        response = llm.invoke(logcheck_query)

        # Parse the response JSON
        response_json = json.loads(response.content)
        
        # Extract service_name, transaction_id, and timestamp
        score = response_json.get('score', '')
        reason = response_json.get('reason', '')
        search = response_json.get('search','')

        response_msg = []
        # Prepare the response message to return
        # response_msg.append ({
        #     "role": "assistant",
        #     "content": response.content
        # })


        print(score)
        print(search)

        if search:
            print("transfer to log retriever agent")
            response_msg.append({
                "role": "assistant", 
                "content": "I will try to find the log from Splunk."
            })

            next_agent = self.transfer_to_log_retriever()
            response = next_agent.execute(query)

            response_msg = response_msg + response.messages

            return Response(
                agent=next_agent,
                messages=response_msg
            )

        if score:
            if int(score) < 65:
                response_msg.append({
                    "role": "assistant", 
                    "content": "I'm sorry, in order for me to investigate, please provide valid ESB transaction logs."
                })

                next_agent = self.transfer_to_triage()
            else:
                print("Valid Log")
                response_msg.append({
                    "role": "assistant",
                    "content": "Thank you for providing the logs. I will route to the Analysis Agent to perform the analysis."
                })
                
                next_agent = self.transfer_to_analysis()

                response = next_agent.execute(query)
                response_msg = response_msg + response.messages

                return Response(
                    agent=next_agent,
                    messages=response_msg
                )

        
        # Return the Response object with the extracted information
        return Response(
            agent=next_agent,
            messages=response_msg
        )
