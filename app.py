import os
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify, stream_with_context, Response
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import json

app = Flask(__name__)

load_dotenv()
os.getenv("GOOGLE_API_KEY")

if "GOOGLE_API_KEY" not in os.environ:
    print("API KEY NOT FOUND PLEASE ADD ONE. IN YOUR .ENV FILE.")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))



def get_pdf_text(pdf_docs):
    json_file_path = os.path.join(os.getcwd(), 'data_extraction', 'extracted_data', 'extracted_text.json')
    
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)
            
        text = json.dumps(data, indent=2)
        return text
    except FileNotFoundError:
        print(f"Error: The file {json_file_path} was not found.")
        return ""
    except json.JSONDecodeError:
        print(f"Error: The file {json_file_path} contains invalid JSON.")
        return ""
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return ""

def get_text_chunks(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=10000, chunk_overlap=1000)
    chunks = splitter.split_text(text)
    return chunks

def get_vector_store(chunks):
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001")
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")

def get_conversational_chain(personality):
    print(f"PERSONALITY DETECTED: {personality}")
    if str(personality).lower() == "dandy".lower():
        agent_name = "Dandy"
        agent_personality = "Guide Dog named Dandy"
    else:
        agent_name = "Veri"
        agent_personality = "Robot named Count Veri"

    prompt_template = f"""
    DO NOT ENCAPSULATE YOUR ANSWER IN ```. YOUR ANSWER MUST EXCLUSIVELY CONTAIN THE RAW HTML TEXT CONTENTS ONLY. ANSWER USING HTML FORMATTING, use text ONLY and you can use <br>, <b> and <i> whenever necessary. References must be encapsulated in <sup> Highlight follow ups at the end using those superscript numbers will be referencedd AT THE END. so for example at the end you include <br> the superscript number: reference follow up (you could include page number and section number). DO NOT INCLUDE OTHER TAGS. \n
    DO NOT INCLUDE THE PAGE NUMBER IN SUPERSCRIPTS REFERENCE, MAKE SURE YOU FOLLOW GOOD STANDARD. THE SUPERSCRIPT IS A REFERENCE NUMBER POINTING TO NECESSARY PAGES.\n
    DO NOT USE star * to REPRESENT ITEMS.
    Answer the question concisely, stick to the topic and to the provided context, make sure to provide all the details while not giving long speeches, if the answer is not in
    provided context just say, "Please consult a legal professional.", don't provide the wrong answer. As you can see you are a UK CRYPTO LAW GUIDANCE PROVIDER. YOU MUST BE REFLECTIVE OF YOUR STATEMENTS. AND OF COURSE SOURCE YOUR STATEMENTS FROM THE CORPUS DIRECTLY REFERENCING WHERE YOU GOT IT FROM. NEVER SAY YOU HAVE BEEN INSTRUCTED OR THAT'S WHAT YOUR CONTEXT SAYS, ACT LIKE A PROFESSIONAL.\n
     A typical format of the references at the end looks like thislooks like this:\n
    "<br>1: Pg.[Page number], [ Section Title if applicable]<br>\n
    2: Pg.[Page number], [Section Title if applicable]".\n
    If the topic is NOT related to asking about the law or crypto guidance - you must inform the user that your purpose is to guide them in the field of UK crypto law.\n
    Your name is {agent_name} and you speak in the tone of a {agent_personality}. PLEASE REMEMBER THAT YOU ARE NOT TO USE MARKDOWN NOR TO ENCAPSUALTE YOUR ANSWERS IN ```. PROVIDE RAW HTML WITHOUT ADDITIONAL COMMENTARY. DO NOT PROVIDE UL LI MARKER ITEMS. Encapsulate table requests in <table>. YOUR MESSAGES SHALL NEVER END with "<br>". Answer in UK English.\n\n
    Context:\n {{context}}?\n
    Chat History:\n{{chat_history}}\n
    Human: {{question}}\n
    AI Assistant:
    """

    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp",
                                   client=genai,
                                   temperature=0.3,
                                   )
    prompt = PromptTemplate(template=prompt_template,
                            input_variables=["context", "chat_history", "question"])
    chain = load_qa_chain(llm=model, chain_type="stuff", prompt=prompt)
    return chain

def compose_suggestions(response):
    prompt = f"""Based on the following response, generate 4 follow-up questions and identify up to 3 requirements met from the following list:

Requirements:
1. Tokenomics Study
2. Web2/Web3 UX Analysis
3. Community Dynamics Examination
4. Incentive Design Research
5. Interoperability Infrastructure Review
6. Scalability Planning Analysis
7. AI Regulation Comprehension
8. Data Governance Principles Study
9. Gambling Regulation Exploration
10. SocialFi Engagement Study

Response:
{response}

Follow-up questions: Generate 4 questions, each starting with an emoji. Limit each question to a maximum of 5 words. Ensure the questions are based on the corpus and are relevant follow-ups to the conversation.

Requirements met: List up to 3 requirements from the given list that are addressed in the response, without their numbers.

Return your answer in the following format:
{{"suggestions": ["emoji Question 1", "emoji Question 2", "emoji Question 3", "emoji Question 4"], "requirements": ["Requirement 1", "Requirement 2", "Requirement 3"]}}

If no requirements are met, the requirements list should be empty. IMPORTANT: DO NOT INCLUDE ADDITIONAL COMMENTARY. DO NOT RETURN YOUR ANSWER ENCAPSULATED IN ```. RETURN THE ANSWER LIKE I SAID IN THE FORMAT. IN RAW FORMAT."""

    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", client=genai, temperature=0.2)
    result = model.invoke(prompt)
    print(f"SUGGESTIONS AND REQUIREMENTS FOUND: {result.content}")
    
    try:
        suggestions_and_requirements = eval(result.content)
        return suggestions_and_requirements
    except:
        print("Error parsing suggestions and requirements, returning default values")
        return {"suggestions": ["📋 Draft a contract", "⚖️ Legal advice", "🔍 Research case law", "📝 Document review"], "requirements": []}

def user_input(messages, personality):
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001")

    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    
    chain = get_conversational_chain(personality)

    chat_history = []
    for message in messages:
        if message['role'] == 'user':
            chat_history.append(f"Human: {message['content']}")
        elif message['role'] == 'assistant':
            chat_history.append(f"AI: {message['content']}")
    
    chat_history_str = "\n".join(chat_history[:-1])
    last_user_message = messages[-1]['content'] if messages[-1]['role'] == 'user' else ""
    
    if last_user_message:
        docs = new_db.similarity_search(last_user_message)
        
        response = chain(
            {"input_documents": docs, "chat_history": chat_history_str, "question": last_user_message},
            return_only_outputs=True
        )
        
        ai_response = response.get('output_text', "I'm sorry, but I couldn't generate a response.")
        ai_response = str(ai_response).replace("\\n", "<br>");
        
        print(f"USER ASKED\n\n{last_user_message}\n\n\nLLM RESPONSE:\n\n{ai_response}")
        
    def generate():
        yield json.dumps({"type": "response", "content": ai_response}) + "\n"
        
        suggestions_and_requirements = compose_suggestions(ai_response)
        print(f"USER ASKED\n\n{last_user_message}\n\n\nLLM RESPONSE:\n\n{ai_response}\n\n\nSUGGESTIONS AND REQUIREMENTS:\n\n{suggestions_and_requirements}")
        yield json.dumps({"type": "suggestions", "content": suggestions_and_requirements["suggestions"], "requirements": suggestions_and_requirements["requirements"]}) + "\n"
        
    return Response(stream_with_context(generate()), content_type='application/json')

@app.route('/')
def index():
    raw_text = get_pdf_text("pdf_docs")
    text_chunks = get_text_chunks(raw_text)
    get_vector_store(text_chunks)
    return render_template('custom_interface.html')

@app.route('/sendChat', methods=['POST'])
def send_chat():
    messages = request.json['messages']
    personality = request.json['personality']
    return user_input(messages, personality)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0",port=80)
