import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from agent_cover_letter.tools.WordsCount import WordCountTool
from agent_cover_letter.tools.CharCount import CharacterCountTool
from langchain_groq import ChatGroq
from crewai_tools import FileReadTool, FileWriterTool, DirectoryReadTool
from pydantic import BaseModel, Field

file_reader_tool = FileReadTool()
directory_reader_tool = DirectoryReadTool("output")
file_writer_tool = FileWriterTool()
words_count_tool = WordCountTool()
char_count_tool = CharacterCountTool()

class CoverLetter(BaseModel):
    body: str = Field(..., description="Content of the cover letter")

class RecipientAndSubject(BaseModel):
    recipient: dict = Field(..., description="Information about the recipient (company)")
    subject: str = Field(..., description="Subject line of the cover letter")

@CrewBase
class AgentCoverLetterCrew():
    """AgentCoverLetter crew"""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self) -> None:
        self.groq_llm = ChatGroq(model_name="llama-3.1-70b-versatile")

    @agent
    def job_analyst_and_personalization_writer(self) -> Agent:
        return Agent(
            config=self.agents_config['job_analyst_and_personalization_writer'],
            llm=self.groq_llm,
            allow_delegation=False,
            verbose=True
        )
    
    @agent
    def info_extraction_and_formatting_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['info_extraction_and_formatting_specialist'],
            llm=self.groq_llm,
            allow_delegation=False,
            verbose=True
        )

    @task
    def job_analysis_and_personalization_task(self) -> Task:
        return Task(
            config=self.tasks_config['job_analysis_and_personalization_task'],
            output_json=CoverLetter,
            output_file="output/cover_letter.json"
        )

    @task
    def optimal_recipient_task(self) -> Task:
        return Task(
            config=self.tasks_config['optimal_recipient_task'],
            output_json=RecipientAndSubject,
            output_file="output/RecipientAndSubject.json"
        )

    @crew
    def crew(self) -> Crew:
        """Creates the AgentCoverLetter crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )