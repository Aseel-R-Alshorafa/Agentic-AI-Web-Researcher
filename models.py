from typing import TypedDict,Optional,List,Dict,Any

from langchain_openai import ChatOpenAI
from typing import List, Dict, Any, TypedDict, Optional
from dotenv import load_dotenv
import os

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Define typed dictionaries for state handling

class AssistantInfo(TypedDict):
    user_question:str
    assistant_type:str
    assistant_instruction:str 
    
class SearchQuery(TypedDict):
    user_question:str
    search_query:str

class SearchResult(TypedDict):
    search_url:str
    user_question:str
    search_query:str
    is_fallback:Optional[bool]
    
class SearchSummary(TypedDict):
    summary:str
    result_url:str
    user_question:str
    is_fallback:Optional[bool]
    
    
class Report(TypedDict):
    report:str
    
    
class ResearchState(TypedDict):
    user_question: str
    assistant_info: Optional[AssistantInfo]
    search_queries: Optional[List[SearchQuery]]
    search_results: Optional[List[SearchResult]]
    search_summaries: Optional[List[SearchSummary]]
    research_summary: Optional[str]
    final_report: Optional[str]
    used_fallback_search: Optional[bool]
    relevance_evaluation: Optional[Dict[str, Any]]
    should_regenerate_queries: Optional[bool]
    iteration_count: Optional[int]




def get_llm():
    return ChatOpenAI(openai_api_key=openai_api_key,
                 model_name="gpt-5-nano")