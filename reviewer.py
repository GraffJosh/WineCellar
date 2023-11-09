from openai import OpenAI


class Reviewer:
    def __init__(self, api_key="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") -> None:
        self.client = OpenAI(
            api_key=api_key, max_retries=5, organization="org-wFj0zUFZz9n48pp48II4mZJW", timeout=15
        )
        self.reviews = {}
        self.totalTokens = 0

    def sendRequest(self, inMessages):
        response = "Sorry, I don't know about that!"
        response_status = False
        try:
            completion = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=inMessages,
                temperature=1,
                max_tokens=256,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )
            self.totalTokens += completion.usage.total_tokens
            response = completion.choices[0].message.content
            response_status = True
        except BaseException as error:
            print("Error connecting to OpenAI: ", error)

        return {"status": response_status, "response": response}

    def getReview(self, inItemName):
        if inItemName not in list(self.reviews.keys()):
            request_messages = [
                {
                    "role": "system",
                    "content": "You are a relaxed sommelier, who keeps reviews short, sweet, and interesting.",
                },
                {
                    "role": "user",
                    "content": "Please provide tasting notes on: {}".format(inItemName),
                },
            ]
            response = self.sendRequest(inMessages=request_messages)
            text = response["response"]
            if response["status"]:
                self.reviews[inItemName] = response
        else:
            print("I've already seen this item!")
            text = self.reviews[inItemName]

        return text
