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
- **AI/ML**: LangChain, LangGraph, OpenAI
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
- OpenAI API key

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
- I was also testing amazon q with this setup, however only thing that was generated by amazon q are the routes for matrix validation. All other code was written by me
- I did a lot of playing around here, as i was inventing use cases, and i did not remove that code as it's already in. If need be i can remove it in a different branch if required
- notebooks hold some tests of mine for different use cases and are completely irrelevant for this project
- additionally agents also hold different tests me creating agents for different purposes. Only relevenant one is validator_agent in langchain that holds the code run here

## Running Evaluations with Inspect AI

### Prerequisites
- Install Inspect AI: `pip install inspect-ai`
- Ensure evaluation datasets are available in `evaluations/` directory

### Evaluation Judge is LLM
Evaluation is done with LLM as the judge. Very important part of evaluation process and generally validation is completeness
level which we evaluate against heavily.
- ```matrix_evaluation.py``` is the file containing inspect ai based evaluation scorer and solver running our langchain code

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