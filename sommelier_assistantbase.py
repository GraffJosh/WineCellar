from openai import OpenAI


class Reviewer:
    def __init__(self, api_key="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") -> None:
        self.client = OpenAI(api_key=api_key, timeout=5)
        self.reviews = {}

        try:
            self.sommelier = self.client.beta.assistants.retrieve(
                assistant_id="asst_VzhGdawm2bTk8vCMNO1iKMdj"
            )
            self.request_thread = self.client.beta.threads.create()
            introduction = self.client.beta.threads.messages.create(
                thread_id=self.request_thread.id,
                role="user",
                content="My name is Josh and I like wine.",
            )
            print(self.sommelier)
        except BaseException as error:
            print("Error connecting to OpenAI: ", error)

    def sendRequest(self, inRequestString):
        wineBottle = self.client.beta.threads.messages.create(
            thread_id=self.request_thread.id,
            role="user",
            content="inRequestString",
        )
        request = self.client.beta.threads.runs.create(
            thread_id=self.request_thread.id,
            assistant_id=self.sommelier.id,
        )
        response = self.client.beta.threads.runs.retrieve(
            thread_id=self.request_thread.id, run_id=request.id
        )
        # response = self.client.chat.completions.create(
        #     model="gpt-4",
        #     messages=[{"role": "user", "content": inRequestString}],
        #     temperature=1,
        #     max_tokens=256,
        #     top_p=1,
        #     frequency_penalty=0,
        #     presence_penalty=0,
        # )
        return response

    def getReview(self, itemName):
        if itemName not in list(self.reviews.keys()):
            request_string = "Please give me tasting notes on {}".format(itemName)
            response = self.sendRequest(inRequestString=request_string)
        else:
            response = self.reviews[itemName]

        return response
