import requests
from bs4 import BeautifulSoup
import urllib.parse
import openai
import string

# Example usage
question = "Where is my closest mcdonalds"
full_question = f"If you do not know the answer or do not have access to that information please simply reply with 'NO' with no symbols or other characters and nothing else. My question: {question}"
openai.api_key = 'TEST'


def generate_gpt_response(messages):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=2000,
        n=1,
        stop=None,
        temperature=0.5,
    )
    return response.choices[0].message['content'].strip()

simple_gpt_question = generate_gpt_response([
    {"role": "user", "content": full_question},
])

print(f"{simple_gpt_question}")

def get_page_text(url):
    # Send a GET request to the page URL
    response = requests.get(url)
    response.raise_for_status()

    # Extract the text content from the HTML response
    soup = BeautifulSoup(response.text, "html.parser")
    page_text = soup.get_text()

    # Filter the text by removing duplicate lines and empty lines
    lines = page_text.splitlines()
    unique_lines = set(lines)
    filtered_lines = [line for line in unique_lines if line.strip()]

    return "\n".join(filtered_lines)

def search_query(query):
    # Prepare the search query
    search_query = query.replace(" ", "+")
    search_url = f"https://www.google.com/search?q={search_query}"

    # Send a GET request to the search engine
    response = requests.get(search_url)
    response.raise_for_status()

    # Extract the first URL from the search results
    soup = BeautifulSoup(response.text, "html.parser")

    snippets = []
    # Look for normal search results
    search_results = soup.select('.kCrYT')
    for result in search_results:
        text = result.get_text()
        if text:
            snippets.append(text)

    # Look for featured snippet
    featured_snippet = soup.select_one('.BNeawe.iBp4i.AP7Wnd')
    if featured_snippet:
        snippets.append(featured_snippet.get_text())

    # Combine the snippets
    page_text = "\n".join(snippets)

    return page_text


RETRIES = 5  # maximum number of retries
rephrase_question = "Rephrase this question so that google can find the answer"

table = str.maketrans('', '', string.punctuation)  # create punctuation removal table

for i in range(RETRIES):
    if simple_gpt_question.lower() == "no" or "I'm sorry, as an AI language model" in simple_gpt_question:
        page_text = search_query(question)
        if page_text:
            aihelper = [{"role": "user", "content": f"Based on the following data I found: {page_text}, can you answer: {question}"}]
            chain_of_thought_response = generate_gpt_response(aihelper)
            print(f"Updated ChatGPT Response: {chain_of_thought_response}\n")
            if "I'm sorry, as an AI language model" not in chain_of_thought_response or "As an AI language model" in chain_of_thought_response:
                break  # break if the model was able to answer the question
            else:
                # If the model was unable to answer the question, ask it to rephrase the question for Google search
                new_question = f"{rephrase_question} my question is {question}"
                print(f"{new_question}")
                aihelper = [{"role": "user", "content": new_question}]
                question2 = generate_gpt_response(aihelper)
                question2 = question2.translate(table)  # remove punctuation from the rephrased question
                print(f"New question for Google: {question2}")
                question = question2  # update the question with the rephrased and punctuation-removed version
        else:
            print("No search results found.")
            break
else:
    print(f"After {RETRIES} retries, a suitable answer was not found.")
