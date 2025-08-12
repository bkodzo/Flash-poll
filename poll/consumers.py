from channels.generic.websocket import AsyncJsonWebsocketConsumer

class VoteConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.slug = self.scope["url_route"]["kwargs"]["slug"]
        self.group_name = f"poll_{self.slug}"

        #join reddis group 
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)


    #handle votes updates from group
    async def vote_update(self, event):
        #event = {"type": "vote.update", "choice": 5, "votes": 8}
        await self.send_json(event)


        