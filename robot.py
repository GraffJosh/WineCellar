from openai import OpenAI
from collections import deque
import time
import httpx
import logging


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

        self.conversationHistory = deque(maxlen=self.config.HISTORY_LENGTH)
        self.logging = False
        if self.logging:
            self.init_logger
        self.client = OpenAI(
            api_key=inApiKey,
            max_retries=3,
            organization=inOrganization,
            timeout=self.config.TIMEOUT,
        )
        self.client.timeout = self.config.TIMEOUT
        self.reviews = {}
        self.maxTokens = self.config.MAX_TOKENS
        self.totalTokens = 0
        self.lengthTolerance = 20
        self.lastResponse = {}
        self.lastRequestTime = time.time()
        self.historyTimeout = self.config.HISTORY_TIMEOUT
        self.abort = False

    def init_logger(self):
        logging.basicConfig(
            format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            level=logging.DEBUG,
        )

    def __del__(self):
        self.client.close()

    def setClientTimeout(self, timeout):
        self.client.timeout = timeout
        self.timeout = timeout

    def setMaxTokens(self, inMaxTokens):
        print("set max tokens: ", inMaxTokens)
        self.maxTokens = inMaxTokens

    def getLastResponse(self):
        return self.last_response

    def resetConversation(self):
        self.conversationHistory.clear()

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

    def sendRequest(self, inMessages=[]):
        response = "Sorry, I don't know about that!"
        response_status = False
        if time.time() - self.lastRequestTime > self.historyTimeout:
            print("History Timeout: resetting history")
            self.resetConversation()
        else:
            print("History active, entries: ", self.conversationHistory.count())
        self.lastRequestTime = time.time()
        try:
            print(inMessages)
            completion = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=inMessages,
                temperature=1,
                max_tokens=self.maxTokens,
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

    def liveResponse(self, inMessages=[], inPrintFunction=None, inStatusFunction=None):
        response = {}
        response["status"] = False
        response["response"] = ""
        if time.time() - self.lastRequestTime > self.historyTimeout:
            print("History Timeout: resetting history")
            self.resetConversation()
        self.lastRequestTime = time.time()
        if inStatusFunction:
            inStatusFunction("generating")
        try:
            for chunk in self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=inMessages,
                max_tokens=self.maxTokens,
                stream=True,
            ):
                content = chunk.choices[0].delta.content
                # print(content)
                if content:
                    response["response"] += content
                    response["status"] = True
                    inPrintFunction(content)
                if self.abort:
                    inPrintFunction("\r\nSorry, I'll stop now!")
                    self.abort = False
                    return response
        except BaseException as error:
            print("Error connecting to OpenAI: ", error)

        if inStatusFunction:
            inStatusFunction("ready")
        return response

    def getTextCompletion(self, text, inPrintFunction=None, inStatusFunction=None):
        request_messages = [{"role": "system", "content": self.config.INITIAL_MESSAGE}]
        if self.conversationHistory:
            request_messages.extend(self.conversationHistory)
        request_messages.append(
            {
                "role": "user",
                "content": "{}".format(text),
            },
        )
        if inPrintFunction is not None:
            response = self.liveResponse(
                inMessages=request_messages,
                inPrintFunction=inPrintFunction,
                inStatusFunction=inStatusFunction,
            )
        else:
            response = self.sendRequest(inMessages=request_messages)
        if response["status"]:
            self.conversationHistory.append(
                {
                    "role": "user",
                    "content": "{}".format(text),
                },
            )
            self.conversationHistory.append(
                {
                    "role": "user",
                    "content": "{}".format(response["response"]),
                },
            )
        return response

    def respondTo(
        self, inText="", inPrintFunction=None, completionFunction=None, inStatusFunction=None
    ):
        result = self.getTextCompletion(
            inText, inPrintFunction=inPrintFunction, inStatusFunction=inStatusFunction
        )
        if completionFunction:
            completionFunction()
        return result["response"]

    def abortResponse(self):
        self.abort = True
