# Morpheus @ HTEC

An AI-powered skill matrix validation system that generates targeted questions to assess and validate engineers' technical expertise through intelligent conversations.
The grading agent does not grade the answers it only validates are the answers correct or not based on provided answer within the context and generated questions

## User Matrix Validation Process

Morpheus employs a sophisticated multi-agent system to validate user skill claims through dynamic question generation and assessment.

### Question Generation Process

1. **Skill Analysis**: System analyzes user's claimed expertise level for specific skills
2. **Dynamic Question Creation**: AI generates targeted questions based on:
   - Claimed expertise level (1-7 scale)
   - Skill domain and complexity
   - Industry best practices and real-world scenarios 
   - For this generation o3-mini has been used, as 4o and 4o-mini are extremely bad and mostly display the same questions no matter the difficulty or simplicity of the prompt

3. **Question Validation**: Generated questions are validated for:
   - Appropriate difficulty level
   - Relevance to claimed expertise
   - Clear assessment criteria and provided necessary assignment knowledge

### User Validation Question Assignment

**Assignment Process:**
1. **Skill Prioritization**: System identifies which skills need validation based on and assigns to the user specific questions designed for this level of knowledge and specific skill

2. **Question Sequencing**: Questions are randomly choosen generally, however as this is POC they are displayed and asking for a validation

### Validator Agent Grading System

**Grading Agent Architecture:**
The Grading Agent uses a multi-dimensional assessment approach to evaluate user responses and assign expertise levels.

**Grading Process:**

1. **Response Analysis**:
   - Technical accuracy assessment
   - Depth of understanding evaluation
   - Comparison to the answer

2. **Evidence Collection**:
   - Specific examples provided
   - Problem-solving approach
   - Tool and technology familiarity
   - Real-world experience indicators

3 **Confidence Scoring**:
   - High confidence: Clear evidence supporting claimed level
   - Medium confidence: Some evidence with minor gaps
   - Low confidence: Insufficient evidence, requires additional validation

**Validation Criteria by Level:**
- **Technical Knowledge**: Depth and accuracy of technical concepts
- **Practical Experience**: Real-world application examples
- **Problem Solving**: Approach to complex scenarios
- **Best Practices**: Industry standard awareness
- **Communication**: Ability to explain concepts clearly

## Core Components

- **Question Generator**: Creates targeted assessment questions
- **Grading Agent**: Evaluates responses and assigns expertise levels
- **Feedback Agent**: Provides constructive guidance for skill improvement

## Tech Stack

- **Backend**: FastAPI with Python 3.13
- **Database**: PostgreSQL with pgvector for embeddings
- **AI/ML**: LangChain, LangGraph, OpenAI through LiteLLM. GPT-4o is mostly used, o3-mini for generating questions and GTP-4.1 for backup if GPT-4o starts acting up. gpt-4o-mini has shown to be unreliable for complex task and complex state. Utilizing ReAcT type loop to investigate and validate expertise levels.
- **Caching**: Redis
- **Task Queue**: Celery
- **Observability**: Langtrace
- **Prompt Library**: Langtrace
- **Metrics Library**: Langtrace
- **Evaluation Library**: Inspect AI

## Expertise Levels

The system recognizes 7 levels of expertise:

1. **Not Informed**: No prior knowledge
2. **Informed Basics**: Basic concept understanding
3. **Informed in Details**: Deep strategic understanding
4. **Practice and Lab Examples**: Practical application ability
5. **Production Maintenance**: Production environment maintenance
6. **Production from Scratch**: Full system setup capability
7. **Educator/Expert**: Teaching and thought leadership level

## Getting Started

### Prerequisites

- Python 3.13
- Docker and Docker Compose
- LiteLLM API key

### Installation

1. Clone the repository
2. Install dependencies: `pipenv install`
3. Set up environment variables in `.env`
4. Start services: `docker-compose up -d`
5. Run migrations: `alembic upgrade head`
6. Start the application: `python main.py`

### API Access

- **Main API**: http://localhost:8000
- **FE Application**: http://localhost:5173
- **Langtrace prompts and observability tool**: http://localhost:3000

# How to use
- Start the docker compose with ```docker-compose up -d or docker compose up -d```. This will start all the required applications and setup the database for this application. Application is not completed on the FE side as it has a lot of possibilities and can be playeed around for ages
- When initially loading application you will be presented with users you can choose you are logging in as. Please choose `Daniel Martinez` as db has been setup for this use case.
- As i've created multiple samples generating multiple questions that can be created for each of the taxonomies will throw more than 10 k results to LiteLLM side which would be expensive to create in this case for POC. That's why please choose Daniel Martinez, as he has setup
- You have validation questions there. Which is the AI that can be tested against.
- The system will preserve the state of the messages so it can be revisited after.

# How it was built
- FE was fully vibe coded without any manual fixes from me
- I was also testing amazon q with this setup, however only thing that was generated by amazon q are the routes for matrix validation and initial README to save me the time for writing it fully. All other code was written by me
- I did a lot of playing around here, as i was inventing use cases, and i did not remove that code as it's already in. If need be i can remove it in a different branch if required
- notebooks hold some tests of mine for different use cases and are completely irrelevant for this project
- additionally agents also hold different tests me creating agents for different purposes. Only relevenant one is validator_agent in langchain that holds the code run here

## Running Evaluations with Inspect AI

### Prerequisites
- Install Inspect AI: `pip install inspect-ai`
- Ensure evaluation datasets are available in `evaluations/` directory

### Evaluation datasets
Two datasets are available for full evaluation
- ```evaluation_dataset.csv``` - most examples around 200 for full evaluation of the entire langgraph
- ```evaluation_dataset_small.csv``` - some examples around 10 for full evaluation for smaller evaluation level

### Evaluation Judge is LLM
Evaluation is done with LLM as the judge. Very important part of evaluation process and generally validation is completeness
level which we evaluate against heavily.
- ```matrix_evaluation.py``` is the file containing inspect ai based evaluation scorer and solver running our langchain code
- Multiple evaluations exist. One for entire langgraph that tests entire process and evaluates against it
- Individual evaluations for each of the agents/llm invokations for grading, reflection etc...

### Running Evaluations

```bash
export PYTHONPATH=/your_local_path_of_the_root_of_project/:$PYTHONPATH
inspect eval matrix_evaluation.py@matrix_validation_eval
```

### Checking the evaluations
To check the evaluation results you can use default Inspect AI method
```bash
inspect view
```

This will start a local UI of inspect ai where you can see evaluation results

### Evaluations: 
- For 200 cases stated in the example there is the precision around 85% for all the cases there.
- accuracy is the most important metrics here, while factuality or similar metrics are not that important in my view!

### Why Inspect AI for Eval?
I can make simple evaluations without any framework i can also use deep eval or inspect ai

**Reason why inspect AI was choosen was because it's deeply integrated with langtrace and it can be displayed within langtrace.
For this project this was not done as it's an overkill, but when building complex systems it can be very usefull.**

**Additionally as this POC all the prompts are under single project without division of test, dev and other environments, which can be problematic in real scenarios, however this can easily be done with different projects within langtrace. While i have not made this division as again this is POC it's easy to make this separation with introduction of langtrace or something like langfuse or similar observability platforms**

### What is left
This is a POC and a lot of things can be done here

For AI:
- Knowledge base can be enriched substantially and as well the question generation! Reason why i have not done this is the i'm uncertain of level and depth of questions are required per each of the level or experience
- Additional RAG pipelines can be added easily through SQL or vector dbs and agentic tool calls to call on additional quidance or preferences from the users (internal company guidance) to establish specific flows and enrich the prompt to tightly control the grading level or similar. This specific problem is very taste based, and my taste would differ than everyone elses. However i see a lot of possible upgrades in this case. I've partially added this through rules in Matrix Questions, however again this can be done in million ways
- Fully agentic multi agent architectures like supervisor or network multiagent systems are more than possible here, and would even be preferential on more level of details and more guidance needs. However for this sample and POC are defenitelly an overkill and create a problem of increasing latency substantionally
- MCP tooling. Just not needed in this case and POC, however would benefit here as tooling would be interchangeable
- A2A as well, just an overkill for this case and POC.
- General tool usage here for different agents. I do not see the need for it. I can put into langgraph state all the required data, only thing would be the need for if i'm getting the preferences, and i've explained here why i have not added that. This is something I'm most skeptic of should i add or not in this example

For Application:
- This is a never ending story what can be added. A lot of funcitonalities is not finished
- We can add detail analytics
- We can add pipelines for getting the data
