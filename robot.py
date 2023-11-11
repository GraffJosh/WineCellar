from openai import OpenAI


class Robot:
    def __init__(self, inApiKey=None, inOrganization=None, timeout=15, inConfig="config") -> None:
        try:
            self.config = __import__(inConfig)
            if not inApiKey:
                inApiKey = self.config.openAI_apiKey
            if not inOrganization:
                inOrganization = self.config.openAI_organization
        except BaseException as e:
            print(e)

        self.client = OpenAI(
            api_key=inApiKey, max_retries=5, organization=inOrganization, timeout=timeout
        )
        self.reviews = {}
        self.totalTokens = 0
        self.lengthTolerance = 20
        self.lastResponse = {}

    def getLastResponse(self):
        return self.last_response

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
        self.last_response = {"status": response_status, "response": response}
        return self.last_response

    def getReview(self, inMessages):
        if list(inMessages.keys())[0] not in list(self.reviews.keys()):
            response = self.sendRequest(inMessages=inMessages)
            text = response["response"]
            if response["status"]:
                self.reviews[list(inMessages.keys())[0]] = response
        else:
            print("I've already seen this item!")
            text = self.reviews[list(inMessages.keys())[0]]

        return text

    def getTextCompletion(self, text, length):
        request_messages = [
            {
                "role": "system",
                "content": "Limit to {} +/- %{} words.".format(length, self.lengthTolerance),
            },
            {
                "role": "user",
                "content": "{}".format(text),
            },
        ]
        response = self.sendRequest(inMessages=request_messages)
        return response

    def respondTo(self, inText="", inLength=None):
        if not inLength:
            inLength = len(inText)
        result = self.getTextCompletion(inText, inLength)
        return result["response"]
