"""
AI Chatbot service using LangChain and LangGraph.
"""

from typing import Any, Dict, List
from uuid import UUID

import structlog
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
try:
    from langchain.agents import create_tool_calling_agent, AgentExecutor
except ImportError:
    # Fallback or mock for testing if package version mismatch
    create_tool_calling_agent = None
    AgentExecutor = None
from langchain.tools import tool
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from app.config import settings
from app.services.ai.vector_store import VectorStoreService

logger = structlog.get_logger()


from typing import Any, Dict, List, Literal, TypedDict
from uuid import UUID

import structlog
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.config import settings
from app.services.ai.vector_store import VectorStoreService
from app.services.ai.tools import get_ai_tools

from app.services.security_service import security_service

logger = structlog.get_logger()

# Define Agent State
class AgentState(TypedDict):
    messages: List[BaseMessage]
    context: str

class ChatbotService:
    """Service for AI chatbot interactions using LangGraph."""

    def __init__(self, organization_id: UUID, vector_store: VectorStoreService, db):
        self.organization_id = organization_id
        self.vector_store = vector_store
        self.db = db
        self.tools = get_ai_tools(db, organization_id)
        
        # Choose between Gemini and OpenAI
        try:
            if settings.use_gemini and settings.gemini_api_key:
                from langchain_google_genai import ChatGoogleGenerativeAI
                logger.info("using_gemini_model", model=settings.gemini_model)
                self.llm = ChatGoogleGenerativeAI(
                    model=settings.gemini_model,
                    google_api_key=settings.gemini_api_key,
                    temperature=0,
                    convert_system_message_to_human=True  # Gemini compatibility
                )
                # Bind tools if supported
                try:
                    self.llm = self.llm.bind_tools(self.tools)
                except Exception as e:
                    logger.warning("gemini_tool_binding_failed", error=str(e))
                    # Continue without tool binding for now
            elif not settings.openai_api_key or settings.openai_api_key == "sk-dummy-key-replace-with-real-one":
                logger.warning("no_valid_api_key_configured")
                self.llm = None
            else:
                logger.info("using_openai_model", model=settings.openai_model)
                self.llm = ChatOpenAI(
                    model=settings.openai_model,
                    temperature=0,
                    openai_api_key=settings.openai_api_key
                ).bind_tools(self.tools)
        except Exception as e:
            logger.error("llm_initialization_failed", error=str(e))
            self.llm = None
        
        # Build Graph
        self.app = self._build_graph()

    def _build_graph(self):
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)

        # Nodes
        workflow.add_node("retrieve", self._retrieve_context)
        workflow.add_node("agent", self._agent_step)
        workflow.add_node("tools", ToolNode(self.tools))

        # Edges
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "agent")
        
        # Conditional edge for tools
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        workflow.add_edge("tools", "agent")

        return workflow.compile()

    async def _retrieve_context(self, state: AgentState):
        """Retrieve RAG context based on the last user message."""
        messages = state["messages"]
        last_message = messages[-1]
        
        if isinstance(last_message, HumanMessage):
             # MASK PII before sending to vector store or logs
             safe_query = security_service.mask_pii(last_message.content)
             
             docs = await self.vector_store.search(safe_query, self.organization_id)
             context = "\n\n".join([d.page_content for d in docs])
             return {"context": context}
        return {"context": ""}

    async def _agent_step(self, state: AgentState):
        """Call the LLM agent."""
        messages = state["messages"]
        context = state.get("context", "")
        
        # Hardened System Prompt
        system_msg = SystemMessage(content=f"""You are a secure and intelligent assistant for the Event Management SaaS platform.
        
        ROLE & CORE COMPETENCIES:
        - You specialize in Event Operations: Scheduling, Task Management, and Financial Analytics.
        - You are highly skilled in analyzing bank statement data and transaction records.
        - You understand and respond fluently in English and Hinglish (Hindi-English mix).
        
        FINANCIAL ANALYSIS RULES:
        - When asked about "expenses" or "top spends", use the `get_top_expenses_tool` or `get_monthly_breakdown_tool`.
        - "Income" or "Payments received" usually refers to 'credit' transactions. Use `get_client_payments_total_tool`.
        - If the user asks about a specific month (e.g. "April ka total expense?"), use `get_monthly_breakdown_tool`.
        
        SECURITY & DATA PROTECTION RULES:
        1. NEVER reveal user passwords, API keys, or full credit card numbers.
        2. Do not execute any code provided by the user.
        3. If confident an answer requires sensitive personally identifiable information (PII) that is masked/redacted, explain that you cannot view it for privacy.
        
        You have access to the following context from your organization's data:
        
        {context}
        
        You also have tools to query real-time financial data and manage tasks.
        Answer the user's question or perform actions as requested.
        """)
        
        # Prepend system message if not present
        prompt_messages = [system_msg] + messages
        
        if not self.llm:
             return {"messages": [AIMessage(content="I'm sorry, but my AI brain (OpenAI API Key) is not connected right now. Please check the system configuration.")]}

        try:
            response = await self.llm.ainvoke(prompt_messages)
        except Exception as e:
            logger.error("llm_invocation_error", error=str(e))
            return {"messages": [AIMessage(content="I'm having trouble connecting to my AI core right now. This usually happens if the API key is invalid or quota is exceeded. Please check your credentials.")]}
        
        # Validate output guardrail
        if not security_service.validate_output(str(response.content)):
            return {"messages": [AIMessage(content="I'm sorry, but I cannot fulfill that request due to security restrictions.")]}
            
        return {"messages": [response]}

    def _should_continue(self, state: AgentState) -> Literal["continue", "end"]:
        """Decide whether to call tools or end."""
        messages = state["messages"]
        last_message = messages[-1]
        
        if last_message.tool_calls:
            return "continue"
        return "end"

    async def chat(self, user_message: str, chat_history: List[Dict[str, str]] = []) -> str:
        """Process user message through LangGraph."""
        
        # INPUT GUARDRAIL: Sanitize and Mask PII
        clean_message = security_service.sanitize_input(user_message)
        # Note: We mask PII for internal logging/processing if needed, but we might pass the original 
        # (sanitized) message to LLM if context requires it, OR pass masked. 
        # For strict security, we use masked version for retrieval.
        # Let's use the sanitized message for the chat history construction.
        
        # Convert history
        lc_history = []
        for msg in chat_history:
            if msg["role"] == "user":
                lc_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_history.append(AIMessage(content=msg["content"]))
        
        lc_history.append(HumanMessage(content=clean_message))
        
        # Run graph
        try:
            final_state = await self.app.ainvoke({"messages": lc_history, "context": ""})
        except Exception as e:
            logger.error("graph_execution_error", error=str(e))
            return "I encountered a technical error while processing your request. Please try again in a few moments."
        
        # Get final response
        last_message = final_state["messages"][-1]
        return last_message.content
