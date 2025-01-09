import json
from channels.generic.websocket import AsyncWebsocketConsumer

class SubmissionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("submissions", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("submissions", self.channel_name)

    async def receive(self, text_data):
        pass

    async def submission_update(self, event):
        submission = event['submission']
        await self.send(text_data=json.dumps({
            'submission': submission
        }))