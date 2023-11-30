import phospho
import openai

phospho.init(tick=0.5)
openai_client = openai.OpenAI()


# NOTE: ollama must be running for this to work, start the ollama app or run `ollama serve`
model = "zephyr"  # TODO: update this for whatever model you wish to use


def generate(prompt, context):
    


def main():
    context = []  # the context stores a conversation history, you can use this to make the model more context aware
    while True:
        user_input = input("Enter a prompt: ")
        print()
        context = generate(user_input, context)
        print(phospho.log_queue.events)
        print()


if __name__ == "__main__":
    main()